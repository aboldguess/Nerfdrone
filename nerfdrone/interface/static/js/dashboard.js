/**
 * Mini README: Client-side controller for the Nerfdrone dashboard.
 *
 * Structure:
 *   - State initialisation and helper utilities for fetch and messaging.
 *   - Map integration supporting Leaflet (OpenStreetMap) and Google Maps.
 *   - Form handlers covering route planning, ingestion, classification,
 *     survey comparisons, and annotations.
 *
 * The script keeps all user guidance visible on screen, logs rich debug
 * information to assist operators, and remains extensible for future
 * modules. Each function favours clarity and defensive coding so issues
 * can be diagnosed quickly by engineers in the field.
 */

const state = {
  activeMap: 'osm',
  drawnGeoJson: null,
  leaflet: {
    map: null,
    drawnItems: null,
    overlayLayer: null,
  },
  google: {
    map: null,
    drawingManager: null,
    polygon: null,
    overlay: null,
  },
  surveyCaptures: [],
  finance: {
    snapshot: { income: [], expenses: [] },
    selectedId: null,
  },
};

const logPanel = document.getElementById('survey-debug');

function appendLog(message) {
  const timestamp = new Date().toISOString();
  logPanel.textContent = `${timestamp}: ${message}\n${logPanel.textContent}`;
}

function formatCurrency(value) {
  return new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'GBP' }).format(value);
}

async function safeJsonFetch(url, options = {}) {
  const response = await fetch(url, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = payload.detail || JSON.stringify(payload);
    throw new Error(detail || `Request failed with status ${response.status}`);
  }
  return payload;
}

function setDrawnGeometry(geojson) {
  state.drawnGeoJson = geojson;
  const input = document.getElementById('area-geojson');
  input.value = geojson ? JSON.stringify(geojson) : '';
  appendLog(geojson ? 'Updated capture polygon from map interaction.' : 'Cleared capture polygon.');
}

function initialiseLeafletMap() {
  const mapElement = document.getElementById('leaflet-map');
  if (!mapElement) {
    return;
  }
  state.leaflet.map = L.map(mapElement).setView([51.5007, -0.1246], 16);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19,
  }).addTo(state.leaflet.map);

  state.leaflet.drawnItems = new L.FeatureGroup();
  state.leaflet.map.addLayer(state.leaflet.drawnItems);
  state.leaflet.overlayLayer = L.layerGroup().addTo(state.leaflet.map);

  const drawControl = new L.Control.Draw({
    draw: {
      circle: false,
      polyline: false,
      rectangle: true,
      marker: false,
      circlemarker: false,
      polygon: {
        allowIntersection: false,
        showArea: true,
      },
    },
    edit: {
      featureGroup: state.leaflet.drawnItems,
      edit: true,
      remove: true,
    },
  });
  state.leaflet.map.addControl(drawControl);

  state.leaflet.map.on(L.Draw.Event.CREATED, (event) => {
    state.leaflet.drawnItems.clearLayers();
    state.leaflet.drawnItems.addLayer(event.layer);
    const geojson = event.layer.toGeoJSON();
    setDrawnGeometry(geojson);
  });

  state.leaflet.map.on(L.Draw.Event.EDITED, (event) => {
    const layers = event.layers;
    layers.eachLayer((layer) => setDrawnGeometry(layer.toGeoJSON()));
  });

  state.leaflet.map.on(L.Draw.Event.DELETED, () => setDrawnGeometry(null));
  appendLog('Leaflet map initialised.');
}

function initialiseGoogleMap() {
  const mapElement = document.getElementById('google-map');
  if (!mapElement) {
    return;
  }
  if (!window.google || !window.google.maps) {
    appendLog('Google Maps script not detected. Configure API key to enable.');
    return;
  }

  state.google.map = new google.maps.Map(mapElement, {
    center: { lat: 51.5007, lng: -0.1246 },
    zoom: 16,
    mapTypeId: 'satellite',
  });

  state.google.drawingManager = new google.maps.drawing.DrawingManager({
    drawingMode: google.maps.drawing.OverlayType.POLYGON,
    drawingControl: true,
    drawingControlOptions: {
      position: google.maps.ControlPosition.TOP_CENTER,
      drawingModes: [
        google.maps.drawing.OverlayType.POLYGON,
        google.maps.drawing.OverlayType.RECTANGLE,
      ],
    },
    polygonOptions: {
      fillColor: '#3b82f6',
      fillOpacity: 0.2,
      strokeWeight: 2,
      clickable: true,
      editable: true,
    },
    rectangleOptions: {
      fillColor: '#3b82f6',
      fillOpacity: 0.2,
      strokeWeight: 2,
      editable: true,
    },
  });
  state.google.drawingManager.setMap(state.google.map);

  google.maps.event.addListener(state.google.drawingManager, 'overlaycomplete', (event) => {
    if (state.google.polygon) {
      state.google.polygon.setMap(null);
    }
    state.google.polygon = event.overlay;
    let geojson;
    if (event.type === google.maps.drawing.OverlayType.RECTANGLE) {
      const bounds = event.overlay.getBounds();
      geojson = {
        type: 'Polygon',
        coordinates: [[
          [bounds.getSouthWest().lng(), bounds.getSouthWest().lat()],
          [bounds.getNorthEast().lng(), bounds.getSouthWest().lat()],
          [bounds.getNorthEast().lng(), bounds.getNorthEast().lat()],
          [bounds.getSouthWest().lng(), bounds.getNorthEast().lat()],
          [bounds.getSouthWest().lng(), bounds.getSouthWest().lat()],
        ]],
      };
    } else {
      const path = event.overlay.getPath();
      geojson = {
        type: 'Polygon',
        coordinates: [[
          ...Array.from({ length: path.getLength() }, (_, index) => {
            const point = path.getAt(index);
            return [point.lng(), point.lat()];
          }),
          (() => {
            const point = path.getAt(0);
            return [point.lng(), point.lat()];
          })(),
        ]],
      };
    }
    setDrawnGeometry(geojson);
  });

  appendLog('Google Map initialised.');
}

function toggleMap(provider) {
  state.activeMap = provider;
  document.getElementById('leaflet-map').classList.toggle('hidden', provider !== 'osm');
  document.getElementById('google-map').classList.toggle('hidden', provider !== 'google');
  appendLog(`Switched basemap to ${provider}.`);
}

async function submitRoute(event) {
  event.preventDefault();
  const form = event.target;
  const formData = new FormData(form);
  if (state.drawnGeoJson) {
    formData.set('area_geojson', JSON.stringify(state.drawnGeoJson));
  }
  const output = document.getElementById('route-output');
  try {
    const payload = await safeJsonFetch('/plan-route', { method: 'POST', body: formData });
    output.textContent = JSON.stringify(payload, null, 2);
  } catch (error) {
    output.textContent = `Route planning failed: ${error.message}`;
  }
}

async function submitUpload(event) {
  event.preventDefault();
  const formData = new FormData(event.target);
  const output = document.getElementById('upload-output');
  try {
    const payload = await safeJsonFetch('/ingest-footage', { method: 'POST', body: formData });
    output.textContent = JSON.stringify(payload, null, 2);
  } catch (error) {
    output.textContent = `Upload failed: ${error.message}`;
  }
}

async function runClassification() {
  const output = document.getElementById('classify-output');
  try {
    const payload = await safeJsonFetch('/classify-demo');
    output.textContent = JSON.stringify(payload, null, 2);
  } catch (error) {
    output.textContent = `Classification failed: ${error.message}`;
  }
}

function populateSurveySelects(captures) {
  const baseSelect = document.getElementById('base-capture-select');
  const targetSelect = document.getElementById('target-capture-select');
  [baseSelect, targetSelect].forEach((select) => {
    select.innerHTML = '';
    captures.forEach((capture) => {
      const option = document.createElement('option');
      option.value = capture.capture_id;
      option.textContent = `${capture.name} (${capture.captured_on})`;
      select.appendChild(option);
    });
  });
}

function renderSurveyList(captures) {
  const list = document.getElementById('survey-days');
  list.innerHTML = '';
  captures.forEach((capture) => {
    const item = document.createElement('li');
    item.innerHTML = `<button type="button" data-capture="${capture.capture_id}">${capture.name} – ${capture.captured_on}</button>`;
    item.querySelector('button').addEventListener('click', () => showSurveyDetails(capture));
    list.appendChild(item);
  });
  appendLog('Survey list rendered.');
}

function updateMapOverlay(capture) {
  if (state.leaflet.map && state.leaflet.overlayLayer) {
    state.leaflet.overlayLayer.clearLayers();
    const layer = L.geoJSON(capture.overlay);
    state.leaflet.overlayLayer.addLayer(layer);
    state.leaflet.map.fitBounds(layer.getBounds(), { padding: [20, 20] });
  }
  if (state.google.map && window.google && capture.overlay) {
    if (state.google.overlay) {
      state.google.overlay.setMap(null);
    }
    const coordinates = capture.overlay.geometry.coordinates[0].map(([lng, lat]) => ({ lat, lng }));
    state.google.overlay = new google.maps.Polygon({
      paths: coordinates,
      strokeColor: '#22c55e',
      strokeOpacity: 0.8,
      strokeWeight: 2,
      fillColor: '#22c55e',
      fillOpacity: 0.2,
    });
    state.google.overlay.setMap(state.google.map);
    const bounds = new google.maps.LatLngBounds();
    coordinates.forEach((point) => bounds.extend(point));
    state.google.map.fitBounds(bounds);
  }
}

function showSurveyDetails(capture) {
  const summary = document.getElementById('survey-summary');
  const pointCloud = document.getElementById('point-cloud-link');
  const assetTable = document.getElementById('asset-table');

  summary.textContent = `${capture.name} captured on ${capture.captured_on}. ${capture.asset_count} assets detected.`;
  pointCloud.innerHTML = `<a href="${capture.point_cloud_path}" target="_blank" rel="noopener">Open point cloud export</a>`;

  const table = document.createElement('table');
  table.innerHTML = `
    <thead>
      <tr>
        <th>Asset</th>
        <th>Class</th>
        <th>Volume (m³)</th>
        <th>Notes</th>
      </tr>
    </thead>
    <tbody></tbody>
  `;
  const tbody = table.querySelector('tbody');
  capture.assets.forEach((asset) => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${asset.asset_id}</td>
      <td>${asset.classification}</td>
      <td>${asset.volume_cubic_m.toFixed(2)}</td>
      <td>${asset.annotations.join('; ') || '—'}</td>
    `;
    tbody.appendChild(row);
  });
  assetTable.innerHTML = '';
  assetTable.appendChild(table);
  appendLog(`Loaded survey details for ${capture.capture_id}.`);
  updateMapOverlay(capture);
}

async function loadSurveyDays() {
  try {
    const payload = await safeJsonFetch('/survey-days');
    state.surveyCaptures = payload.captures;
    renderSurveyList(state.surveyCaptures);
    populateSurveySelects(state.surveyCaptures);
  } catch (error) {
    appendLog(`Failed to load survey days: ${error.message}`);
  }
}

async function submitComparison(event) {
  event.preventDefault();
  const formData = new FormData(event.target);
  const output = document.getElementById('comparison-output');
  try {
    const payload = await safeJsonFetch('/compare-captures', { method: 'POST', body: formData });
    output.textContent = JSON.stringify(payload, null, 2);
  } catch (error) {
    output.textContent = `Comparison failed: ${error.message}`;
  }
}

async function submitAnnotation(event) {
  event.preventDefault();
  const formData = new FormData(event.target);
  const output = document.getElementById('annotation-output');
  try {
    const payload = await safeJsonFetch('/annotate-asset', { method: 'POST', body: formData });
    output.textContent = JSON.stringify(payload, null, 2);
    await loadSurveyDays();
  } catch (error) {
    output.textContent = `Annotation failed: ${error.message}`;
  }
}

function setupProfileMenu() {
  const profileButton = document.getElementById('profile-button');
  const profileMenu = document.getElementById('profile-menu');
  profileButton.addEventListener('click', () => {
    const expanded = profileButton.getAttribute('aria-expanded') === 'true';
    profileButton.setAttribute('aria-expanded', (!expanded).toString());
    profileMenu.classList.toggle('open');
  });
}

function setupEventListeners() {
  document.getElementById('route-form').addEventListener('submit', submitRoute);
  document.getElementById('upload-form').addEventListener('submit', submitUpload);
  document.getElementById('classify-button').addEventListener('click', runClassification);
  document.getElementById('comparison-form').addEventListener('submit', submitComparison);
  document.getElementById('annotation-form').addEventListener('submit', submitAnnotation);

  document.querySelectorAll('input[name="map-provider"]').forEach((input) => {
    input.addEventListener('change', (event) => toggleMap(event.target.value));
  });

  const financeForm = document.getElementById('finance-duplicate-form');
  if (financeForm) {
    financeForm.addEventListener('submit', submitFinanceDuplicate);
  }
  const financeClear = document.getElementById('finance-clear-selection');
  if (financeClear) {
    financeClear.addEventListener('click', clearFinanceSelection);
  }
}

window.addEventListener('DOMContentLoaded', () => {
  setupProfileMenu();
  setupEventListeners();
  initialiseLeafletMap();
  initialiseGoogleMap();
  loadSurveyDays();
  loadFinanceTransactions();
});

function renderFinanceTables(snapshot) {
  state.finance.snapshot = snapshot;
  const incomeBody = document.getElementById('income-body');
  const expenseBody = document.getElementById('expense-body');
  if (!incomeBody || !expenseBody) {
    return;
  }

  const renderRows = (tbody, entries) => {
    tbody.innerHTML = '';
    if (!entries.length) {
      const emptyRow = document.createElement('tr');
      emptyRow.innerHTML = '<td colspan="6">No entries recorded yet.</td>';
      tbody.appendChild(emptyRow);
      return;
    }

    entries.forEach((transaction) => {
      const row = document.createElement('tr');
      row.dataset.transactionId = transaction.transaction_id;
      row.innerHTML = `
        <td>${transaction.description}</td>
        <td>${transaction.category}</td>
        <td>${formatCurrency(transaction.amount)}</td>
        <td>${transaction.occurred_on}</td>
        <td>${renderMetadataSummary(transaction.metadata)}</td>
        <td><button type="button" class="duplicate-transaction" data-transaction="${transaction.transaction_id}">Duplicate</button></td>
      `;
      if (state.finance.selectedId === transaction.transaction_id) {
        row.classList.add('selected');
      }
      tbody.appendChild(row);
    });
  };

  renderRows(incomeBody, snapshot.income);
  renderRows(expenseBody, snapshot.expenses);
  bindFinanceDuplicateButtons();
}

function renderMetadataSummary(metadata) {
  const entries = Object.entries(metadata || {});
  if (!entries.length) {
    return '—';
  }
  return entries.map(([key, value]) => `${key}: ${value}`).join(', ');
}

function bindFinanceDuplicateButtons() {
  document.querySelectorAll('.duplicate-transaction').forEach((button) => {
    button.addEventListener('click', () => {
      const transaction = findFinanceTransaction(button.dataset.transaction);
      if (transaction) {
        prepareFinanceForm(transaction);
      }
    });
  });
}

function findFinanceTransaction(transactionId) {
  const { income, expenses } = state.finance.snapshot;
  return [...income, ...expenses].find((entry) => entry.transaction_id === transactionId) || null;
}

function prepareFinanceForm(transaction) {
  const form = document.getElementById('finance-duplicate-form');
  if (!form) {
    return;
  }
  form.source_transaction_id.value = transaction.transaction_id;
  form.description.value = transaction.description;
  form.category.value = transaction.category;
  form.amount.value = transaction.amount;
  form.occurred_on.value = transaction.occurred_on;
  form.transaction_type.value = transaction.transaction_type;
  form.metadata.value = Object.keys(transaction.metadata || {}).length
    ? JSON.stringify(transaction.metadata, null, 2)
    : '';
  state.finance.selectedId = transaction.transaction_id;
  updateFinanceSelectionSummary(transaction);
  highlightFinanceSelection();
}

function clearFinanceSelection() {
  const form = document.getElementById('finance-duplicate-form');
  if (!form) {
    return;
  }
  form.reset();
  form.source_transaction_id.value = '';
  state.finance.selectedId = null;
  updateFinanceSelectionSummary(null);
  highlightFinanceSelection();
}

function updateFinanceSelectionSummary(transaction) {
  const summary = document.getElementById('finance-selection-summary');
  if (!summary) {
    return;
  }
  if (!transaction) {
    summary.textContent = 'Select an entry to duplicate its details.';
    return;
  }
  summary.textContent = `Duplicating ${transaction.transaction_type} ${transaction.transaction_id}. Adjust any fields before saving.`;
}

function highlightFinanceSelection() {
  document.querySelectorAll('#finance-panel tbody tr').forEach((row) => {
    if (row.dataset.transactionId === state.finance.selectedId) {
      row.classList.add('selected');
    } else {
      row.classList.remove('selected');
    }
  });
}

async function loadFinanceTransactions() {
  try {
    const snapshot = await safeJsonFetch('/finance/transactions');
    renderFinanceTables(snapshot);
  } catch (error) {
    const output = document.getElementById('finance-output');
    if (output) {
      output.textContent = `Failed to load finance data: ${error.message}`;
    }
  }
}

async function submitFinanceDuplicate(event) {
  event.preventDefault();
  const form = event.target;
  const output = document.getElementById('finance-output');
  if (!form.source_transaction_id.value) {
    if (output) {
      output.textContent = 'Choose an entry to duplicate before submitting.';
    }
    return;
  }
  const formData = new FormData(form);
  try {
    const payload = await safeJsonFetch('/finance/duplicate', { method: 'POST', body: formData });
    renderFinanceTables(payload.snapshot);
    if (output) {
      output.textContent = JSON.stringify(payload.transaction, null, 2);
    }
    appendLog(`Duplicated transaction ${form.source_transaction_id.value}.`);
  } catch (error) {
    if (output) {
      output.textContent = `Duplication failed: ${error.message}`;
    }
  }
}
