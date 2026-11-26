<script setup>
import { nextTick, onMounted, ref } from 'vue'
import Plotly from 'plotly.js-dist-min'

const csvFiles = ref([])
const selectedCsv = ref('')
const rows = ref([])
const selectedName = ref('')
const isLoading = ref(false)
const isLoadingFiles = ref(true)
const errorMessage = ref('')
const normalizedData = ref(null)
const modelData = ref(null)
const surfaceChart = ref(null)
const agioChart = ref(null)
const reqmChart = ref(null)
const availablePolynomialDegrees = [0, 1, 2, 3]
const estimateYear = ref('')
const estimateKm = ref('')
const estimateResult = ref(null)
const estimateComparisons = ref([])
const isEstimating = ref(false)
const csvFileInput = ref(null)
const isUploadingCsv = ref(false)
const polynomialDegree = ref(2)
const showPolynomialSurface = ref(true)

const currencyFormatter = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
  maximumFractionDigits: 2,
})

const numberFormatter = new Intl.NumberFormat('pt-BR')

async function fetchCsvFiles() {
  isLoadingFiles.value = true
  errorMessage.value = ''

  try {
    const response = await fetch('/api/dados')
    if (!response.ok) throw new Error(`HTTP ${response.status}`)

    const data = await response.json()
    csvFiles.value = data.csv_files ?? []
  } catch (error) {
    errorMessage.value = 'Nao foi possivel carregar os arquivos CSV.'
    console.error(error)
  } finally {
    isLoadingFiles.value = false
  }
}

function openCsvPicker() {
  csvFileInput.value?.click()
}

async function uploadCsv(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return

  isUploadingCsv.value = true
  errorMessage.value = ''

  try {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch('/api/dados/upload', {
      method: 'POST',
      body: formData,
    })
    const data = await response.json()

    if (!response.ok) {
      const missing = data.missing?.length
        ? ` Colunas ausentes: ${data.missing.join(', ')}.`
        : ''
      throw new Error((data.error || 'Nao foi possivel adicionar o CSV.') + missing)
    }

    await fetchCsvFiles()
    selectedCsv.value = data.csv_file
  } catch (error) {
    errorMessage.value = error.message || 'Nao foi possivel adicionar o CSV.'
  } finally {
    isUploadingCsv.value = false
  }
}

async function calculateSelectedCsv() {
  if (!selectedCsv.value) return
  if (!availablePolynomialDegrees.includes(polynomialDegree.value)) {
    errorMessage.value = 'Selecione um grau entre zero e três.'
    return
  }

  isLoading.value = true
  errorMessage.value = ''
  normalizedData.value = null
  modelData.value = null
  showPolynomialSurface.value = true
  estimateResult.value = null
  estimateComparisons.value = []
  if (surfaceChart.value) Plotly.purge(surfaceChart.value)
  if (agioChart.value) Plotly.purge(agioChart.value)
  if (reqmChart.value) Plotly.purge(reqmChart.value)

  try {
    const [dataResponse, normalizationResponse, modelsResponse] = await Promise.all([
      fetch(`/api/dados/${encodeURIComponent(selectedCsv.value)}`),
      fetch(`/api/funcoes/normaliza/${encodeURIComponent(selectedCsv.value)}`),
      fetch(`/api/funcoes/modelos/${encodeURIComponent(selectedCsv.value)}?grau=${polynomialDegree.value}`),
    ])

    if (!dataResponse.ok) throw new Error(`HTTP ${dataResponse.status}`)
    if (!normalizationResponse.ok) throw new Error(`HTTP ${normalizationResponse.status}`)
    if (!modelsResponse.ok) throw new Error(`HTTP ${modelsResponse.status}`)

    const data = await dataResponse.json()
    const normalizationData = await normalizationResponse.json()
    const models = await modelsResponse.json()
    rows.value = (data.rows ?? [])
      .map((row, index) => ({
        ...row,
        agioPolinomial: models.polynomial.agio[index] ?? 0,
      }))
      .sort((left, right) => left.agioPolinomial - right.agioPolinomial)
    selectedName.value = data.csv_file ?? selectedCsv.value
    normalizedData.value = normalizationData.normalized
    modelData.value = models
    await nextTick()
    renderSurfaceChart()
    renderAgioChart()
    renderReqmChart()
  } catch (error) {
    rows.value = []
    normalizedData.value = null
    modelData.value = null
    errorMessage.value = 'Nao foi possivel calcular os dados deste arquivo.'
    console.error(error)
  } finally {
    isLoading.value = false
  }
}

function formatCurrency(value) {
  return currencyFormatter.format(value)
}

function formatKm(value) {
  return `${numberFormatter.format(value)} km`
}

// Os dados normalizados ficam centrados em zero: (x - media) / (max - min).
// Por isso o intervalo nao e [0, 1] e pode ter negativos, ex.: [-0.45, 0.55].
function normalizedRange(values) {
  const numericValues = (values ?? []).map(Number).filter(Number.isFinite)
  if (!numericValues.length) return { min: 0, max: 0 }
  return { min: Math.min(...numericValues), max: Math.max(...numericValues) }
}

function histogram(values) {
  const buckets = Array(10).fill(0)
  const { min, max } = normalizedRange(values)
  const width = max - min

  for (const value of values ?? []) {
    const numericValue = Number(value)
    if (!Number.isFinite(numericValue)) continue

    // Divide o intervalo real [min, max] em 10 faixas
    const bucket = width > 0
      ? Math.min(9, Math.floor(((numericValue - min) / width) * 10))
      : 0
    buckets[bucket] += 1
  }

  const maximum = Math.max(...buckets, 1)
  return buckets.map((count) => ({
    count,
    height: `${Math.max(8, (count / maximum) * 100)}%`,
  }))
}

const axisFormatter = new Intl.NumberFormat('pt-BR', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

function formatAxis(value) {
  return axisFormatter.format(value)
}

function formatStat(value) {
  if (!Number.isFinite(Number(value))) return '-'
  return numberFormatter.format(Number(value))
}

function formatCoefficient(value) {
  if (!Number.isFinite(Number(value))) return '-'
  return Number(value).toFixed(6).replace('-0.000000', '0.000000')
}

function formatReqm(value) {
  if (!Number.isFinite(Number(value))) return '-'
  return currencyFormatter.format(Number(value))
}

function vehicleSituation(agio) {
  if (agio <= -10) return 'Barganha'
  if (agio >= 10) return 'Preço acima do valor estimado'
  return 'Preço justo'
}

function vehicleSituationClass(agio) {
  if (agio <= -10) return 'bargain'
  if (agio >= 10) return 'above'
  return 'fair'
}

function formatAgio(value) {
  if (!Number.isFinite(Number(value))) return '-'
  return `${Number(value) >= 0 ? '+' : ''}${Number(value).toFixed(1).replace('.', ',')}%`
}

function renderReqmChart() {
  if (!reqmChart.value || !modelData.value?.reqm_curve) return

  const { degrees, values } = modelData.value.reqm_curve
  Plotly.react(
    reqmChart.value,
    [{
      type: 'scatter',
      mode: 'lines+markers',
      name: 'REQM',
      x: degrees,
      y: values,
      line: { color: '#7c3aed', width: 2 },
      marker: { color: '#7c3aed', size: 6 },
      hovertemplate: 'Grau %{x}<br>REQM: R$ %{y:,.2f}<extra></extra>',
    }],
    {
      margin: { l: 90, r: 24, b: 55, t: 35 },
      height: 380,
      paper_bgcolor: '#ffffff',
      plot_bgcolor: '#ffffff',
      title: {
        text: 'Raiz do erro quadrático médio por grau do polinômio',
        font: { size: 15, color: '#0f172a' },
      },
      xaxis: {
        title: 'Grau do polinômio (n)',
        range: [0, 30],
        dtick: 2,
        tick0: 0,
      },
      yaxis: {
        title: 'REQM (R$)',
        rangemode: 'tozero',
        separatethousands: true,
      },
    },
    { responsive: true, displaylogo: false },
  )
}

async function estimateVehiclePrice() {
  const year = Number(estimateYear.value)
  const km = Number(estimateKm.value)

  if (!selectedCsv.value || !Number.isFinite(year) || !Number.isFinite(km) || km < 0) {
    errorMessage.value = 'Informe um ano valido e uma quilometragem igual ou superior a zero.'
    return
  }

  isEstimating.value = true
  errorMessage.value = ''

  try {
    const response = await fetch(
      `/api/funcoes/estima/${encodeURIComponent(selectedCsv.value)}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ano: year, km, grau: polynomialDegree.value }),
      },
    )

    if (!response.ok) {
      const data = await response.json()
      throw new Error(data.error || `HTTP ${response.status}`)
    }

    estimateResult.value = await response.json()
  } catch (error) {
    estimateResult.value = null
    errorMessage.value = error.message || 'Nao foi possivel estimar o preço.'
  } finally {
    isEstimating.value = false
  }
}

function addEstimateToComparison() {
  if (!estimateResult.value) return

  estimateComparisons.value = [
    ...estimateComparisons.value,
    {
      id: `${Date.now()}-${estimateComparisons.value.length}`,
      ...estimateResult.value,
    },
  ]
}

function removeEstimate(index) {
  estimateComparisons.value = estimateComparisons.value.filter((_, itemIndex) => itemIndex !== index)
}

function updateSurfaceVisibility() {
  if (!surfaceChart.value) return
  Plotly.restyle(surfaceChart.value, { visible: showPolynomialSurface.value }, [1])
}

function polynomialGrid(value) {
  const ano = value.ano
  const km = value.km
  const coefficients = modelData.value.polynomial.coefficients
  let result = 0
  let index = 0

  for (let degree = 0; degree <= modelData.value.degree; degree += 1) {
    for (let kmExponent = 0; kmExponent <= degree; kmExponent += 1) {
      const anoExponent = degree - kmExponent
      result += (coefficients[index++] ?? 0)
        * (ano ** anoExponent)
        * (km ** kmExponent)
    }
  }
  return result
}

function polynomialFormula() {
  if (!modelData.value) return 'p̂(A, K)'
  const terms = []
  let index = 0

  for (let degree = 0; degree <= modelData.value.degree; degree += 1) {
    for (let kmExponent = 0; kmExponent <= degree; kmExponent += 1) {
      const anoExponent = degree - kmExponent
      let term = `c${index}`
      if (anoExponent > 0) term += `A${anoExponent > 1 ? '^' + anoExponent : ''}`
      if (kmExponent > 0) term += `K${kmExponent > 1 ? '^' + kmExponent : ''}`
      terms.push(term)
      index += 1
    }
  }
  return `p̂(A, K) = ${terms.join(' + ')}`
}

function renderSurfaceChart() {
  if (!surfaceChart.value || !modelData.value) return

  const points = modelData.value.points
  const anoValues = points.ano
  const kmValues = points.km
  const precoValues = points.preco

  const anoMin = Math.min(...anoValues)
  const anoMax = Math.max(...anoValues)
  const kmMin = Math.min(...kmValues)
  const kmMax = Math.max(...kmValues)

  const anoGrid = Array.from(
    { length: 24 },
    (_, index) => anoMin + (index / 23) * (anoMax - anoMin),
  )
  const kmGrid = Array.from(
    { length: 24 },
    (_, index) => kmMin + (index / 23) * (kmMax - kmMin),
  )

  const polynomialSurface = kmGrid.map((km) =>
    anoGrid.map((ano) => polynomialGrid({ ano, km })),
  )

  const scatterTrace = {
    type: 'scatter3d',
    mode: 'markers',
    name: 'Dados observados',
    x: anoValues,
    y: kmValues,
    z: precoValues,
    marker: {
      size: 4,
      color: precoValues,
      colorscale: 'Blues',
      opacity: 0.9,
    },
  }

  const polynomialTrace = {
    type: 'surface',
    name: `Modelo polinomial grau ${modelData.value.degree}`,
    x: anoGrid,
    y: kmGrid,
    z: polynomialSurface,
    colorscale: 'Teal',
    opacity: 0.58,
    showscale: false,
    visible: showPolynomialSurface.value,
  }

  Plotly.react(
    surfaceChart.value,
    [scatterTrace, polynomialTrace],
    {
      margin: { l: 0, r: 0, b: 0, t: 20 },
      height: 520,
      paper_bgcolor: '#ffffff',
      scene: {
        xaxis: { title: 'Ano normalizado' },
        yaxis: { title: 'Km normalizado' },
        zaxis: { title: 'Preço normalizado' },
      },
      legend: {
        orientation: 'h',
        x: 0,
        y: 1,
      },
    },
    { responsive: true, displaylogo: false },
  )
}

function renderAgioChart() {
  if (!agioChart.value || !modelData.value) return

  const agioValues = modelData.value.polynomial.agio.map(Number)
  if (!agioValues.length) return

  const ordered = agioValues
    .map((value, index) => ({ value, index: index + 1 }))
    .sort((left, right) => left.value - right.value)

  const colors = ordered.map(({ value }) => (
    value <= -10 ? '#22c55e' : value >= 10 ? '#ef4444' : '#3b82f6'
  ))

  const minimum = Math.min(...agioValues, -10)
  const maximum = Math.max(...agioValues, 10)

  Plotly.react(
    agioChart.value,
    [{
      type: 'bar',
      x: ordered.map(({ index }) => `#${index}`),
      y: ordered.map(({ value }) => value),
      marker: {
        color: colors,
        line: { color: '#ffffff', width: 0.5 },
      },
      hovertemplate: 'Veículo %{x}<br>Ágio: %{y:.1f}%<extra></extra>',
    }],
    {
      margin: { l: 55, r: 20, b: 55, t: 35 },
      height: 340,
      paper_bgcolor: '#ffffff',
      plot_bgcolor: '#ffffff',
      bargap: 0.18,
      title: {
        text: `Distribuição do ágio - modelo grau ${modelData.value.degree}`,
        font: { size: 15, color: '#0f172a' },
      },
      xaxis: {
        title: 'Veículos (ordenados pela melhor barganha)',
        tickangle: -45,
      },
      yaxis: {
        title: 'Ágio (%)',
        zeroline: true,
        zerolinecolor: '#0f172a',
        zerolinewidth: 2,
        range: [
          Math.min(minimum - 5, -15),
          Math.max(maximum + 5, 15),
        ],
      },
      shapes: [
        {
          type: 'line',
          xref: 'paper',
          x0: 0,
          x1: 1,
          y0: 10,
          y1: 10,
          line: { color: '#ef4444', width: 1.5, dash: 'dash' },
        },
        {
          type: 'line',
          xref: 'paper',
          x0: 0,
          x1: 1,
          y0: -10,
          y1: -10,
          line: { color: '#22c55e', width: 1.5, dash: 'dash' },
        },
      ],
      annotations: [
        {
          xref: 'paper',
          yref: 'y',
          x: 1,
          y: 10,
          text: '+10%',
          showarrow: false,
          xanchor: 'right',
          yanchor: 'bottom',
          font: { color: '#b91c1c', size: 11 },
        },
        {
          xref: 'paper',
          yref: 'y',
          x: 1,
          y: -10,
          text: '-10%',
          showarrow: false,
          xanchor: 'right',
          yanchor: 'top',
          font: { color: '#15803d', size: 11 },
        },
        {
          xref: 'paper',
          yref: 'y',
          x: 1,
          y: 0,
          text: 'Preço justo',
          showarrow: false,
          xanchor: 'right',
          yanchor: 'bottom',
          font: { color: '#1d4ed8', size: 11 },
        },
      ],
    },
    { responsive: true, displaylogo: false },
  )
}

onMounted(fetchCsvFiles)
</script>

<template>
  <main class="page-shell">
    <section class="content">
      <header class="page-header">
        <p class="eyebrow">Analise de mercado</p>
        <h1>Estimar preço de mercado</h1>
      </header>

      <section class="analysis-card" aria-labelledby="csv-title">
        <div class="card-heading">
          <div>
            <p class="step-label">Etapa 1</p>
            <h2 id="csv-title">Selecione o CSV para analise</h2>
          </div>
          <span v-if="csvFiles.length" class="file-count">
            {{ csvFiles.length }} arquivos
          </span>
        </div>

        <div class="controls">
          <label class="select-field" for="csv-select">
            <span>Arquivo CSV</span>
            <select
              id="csv-select"
              v-model="selectedCsv"
              :disabled="isLoadingFiles || csvFiles.length === 0"
            >
              <option value="" disabled>
                {{ isLoadingFiles ? 'Carregando arquivos...' : 'Escolha um arquivo' }}
              </option>
              <option v-for="file in csvFiles" :key="file" :value="file">
                {{ file }}
              </option>
            </select>
          </label>

          <label class="select-field" for="polynomial-degree">
            <span>Grau do polinômio</span>
            <select
              id="polynomial-degree"
              v-model.number="polynomialDegree"
            >
              <option
                v-for="degree in availablePolynomialDegrees"
                :key="degree"
                :value="degree"
              >
                Grau {{ degree }}
              </option>
            </select>
          </label>

          <input
            ref="csvFileInput"
            class="csv-file-input"
            type="file"
            accept=".csv,text/csv"
            @change="uploadCsv"
          >
          <button
            type="button"
            class="add-button"
            :disabled="isUploadingCsv"
            @click="openCsvPicker"
          >
            <span aria-hidden="true">+</span>
            {{ isUploadingCsv ? 'Adicionando...' : 'Adicionar novo' }}
          </button>

          <button
            type="button"
            class="calculate-button"
            :disabled="!selectedCsv || isLoading"
            @click="calculateSelectedCsv"
          >
            {{ isLoading ? 'Calculando...' : 'Calcular' }}
          </button>
        </div>

        <p v-if="errorMessage" class="error-message" role="alert">
          {{ errorMessage }}
        </p>
      </section>

      <details v-if="normalizedData && modelData" class="process-details">
        <summary>
          <span>
            <span class="process-step">Etapa intermediaria</span>
            <strong>Etapas intermediarias do cálculo</strong>
          </span>
          <span class="expand-label">Expandir</span>
        </summary>

        <div class="process-content">
          <section class="intermediate-section">
            <div class="intermediate-heading">
              <span class="part-badge">Parte 1</span>
              <h3>Normalizando os dados</h3>
            </div>
          <p class="process-description">
            Distribuicao dos dados normalizados para os parâmetros utilizados no modelo.
          </p>

          <div class="histograms">
            <article
              v-for="(label, parameter) in {
                ano: 'Ano',
                km: 'Quilometragem',
                preco: 'Preço',
              }"
              :key="label"
              class="histogram-card"
            >
              <div class="histogram-heading">
                <h3>{{ label }}</h3>
                <span v-if="normalizedData[parameter]?.values" class="point-count">
                  {{ normalizedData[parameter].values.length }} pontos
                </span>
              </div>

              <div class="histogram" aria-label="Histograma de dados normalizados">
                <div
                  v-for="(bucket, index) in histogram(normalizedData[parameter]?.values)"
                  :key="index"
                  class="histogram-column"
                  :style="{ height: bucket.height }"
                  :title="`${bucket.count} ponto(s)`"
                />
              </div>
              <div class="axis-labels">
                <span>{{ formatAxis(normalizedRange(normalizedData[parameter]?.values).min) }}</span>
                <span>Normalizado</span>
                <span>{{ formatAxis(normalizedRange(normalizedData[parameter]?.values).max) }}</span>
              </div>

              <div v-if="normalizedData[parameter]?.stats?.length" class="statistics">
                <span>
                  <small>Mínimo</small>
                  {{ formatStat(normalizedData[parameter].stats[0]) }}
                </span>
                <span>
                  <small>Máximo</small>
                  {{ formatStat(normalizedData[parameter].stats[1]) }}
                </span>
                <span>
                  <small>Média</small>
                  {{ formatStat(normalizedData[parameter].stats[2]) }}
                </span>
              </div>
            </article>
          </div>
          </section>
          <section class="intermediate-section">
            <div class="intermediate-heading">
              <span class="part-badge">Parte 2</span>
              <h3>Definindo os modelos e calculando os coeficientes</h3>
            </div>
          <p class="process-description">
            Os coeficientes são obtidos pelas equações normais XᵀXc = Xᵀp,
            resolvendo o sistema normal para o grau selecionado.
          </p>

          <div class="model-grid">
            <article class="model-card">
              <div class="model-heading">
                <span class="model-badge">Modelo</span>
                <h3>Aproximação polinomial grau {{ modelData.degree }}</h3>
              </div>

              <div class="formula-block">
                <span class="formula-label">Modelo</span>
                <p>{{ polynomialFormula() }}</p>
              </div>

              <div class="formula-block">
                <span class="formula-label">Equação normal</span>
                <p>(X<sup>T</sup>X)c = X<sup>T</sup>P</p>
              </div>

              <div class="coefficient-list coefficient-list-large">
                <span v-for="(coefficient, index) in modelData.polynomial.coefficients" :key="index">
                  <small>c{{ index }}</small>
                  {{ formatCoefficient(coefficient) }}
                </span>
              </div>

              <div class="reqm-result quadratic-reqm">
                <span>Raiz do erro quadrático médio (REQM)</span>
                <strong>{{ formatReqm(modelData.polynomial.reqm) }}</strong>
              </div>
            </article>
          </div>

          <article class="surface-card">
            <div class="surface-heading">
              <div>
                <p class="step-label">Visualização 3D</p>
                <h3>Dados e superfícies ajustadas</h3>
              </div>
              <span class="source-name">{{ selectedName }}</span>
            </div>
            <div class="surface-controls" aria-label="Controle das superficies">
              <button
                type="button"
                class="surface-toggle quadratic-toggle"
                :class="{ active: showPolynomialSurface }"
                :aria-pressed="showPolynomialSurface"
                @click="showPolynomialSurface = !showPolynomialSurface; updateSurfaceVisibility()"
              >
                <span aria-hidden="true"></span>
                Superfície grau {{ modelData.degree }}
              </button>
            </div>
            <div ref="surfaceChart" class="surface-chart" aria-label="Grafico tridimensional dos modelos"></div>
          </article>
          </section>
        </div>
      </details>

      <section v-if="rows.length" class="results-card" aria-labelledby="results-title">
        <div class="results-heading">
          <div>
            <p class="step-label">Resultados</p>
            <h2 id="results-title">Dados calculados</h2>
          </div>
          <span class="source-name" :title="selectedName">{{ selectedName }}</span>
        </div>

        <article class="agio-chart-card">
          <div class="agio-chart-heading">
            <div>
              <p class="step-label">Histograma do ágio</p>
              <h3>Ajuste polinomial grau {{ modelData.degree }}</h3>
            </div>
            <div class="agio-legend" aria-label="Legenda do histograma">
              <span><i class="legend-green"></i>Barganha</span>
              <span><i class="legend-blue"></i>Preço justo</span>
              <span><i class="legend-red"></i>Acima do valor</span>
            </div>
          </div>
          <div ref="agioChart" class="agio-chart" :aria-label="`Histograma do agio pelo ajuste grau ${modelData.degree}`"></div>
        </article>

        <article class="agio-chart-card reqm-chart-card">
          <div class="agio-chart-heading">
            <div>
              <p class="step-label">Qualidade do ajuste</p>
              <h3>Raiz do erro quadrático médio (REQM) — graus 0 a 30</h3>
            </div>
          </div>
          <div ref="reqmChart" class="agio-chart" aria-label="Gráfico da raiz do erro quadrático médio dos polinômios de grau zero a trinta"></div>
        </article>

        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th scope="col">Ano</th>
                <th scope="col">Quilometragem</th>
                <th scope="col">Preço</th>
                <th scope="col">Ágio</th>
                <th scope="col">Situação</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, index) in rows" :key="`${row.ano}-${row.km}-${index}`">
                <td><span class="year-badge">{{ row.ano }}</span></td>
                <td>{{ formatKm(row.km) }}</td>
                <td class="price-cell">{{ formatCurrency(row.preco) }}</td>
                <td class="agio-cell">{{ formatAgio(row.agioPolinomial) }}</td>
                <td>
                  <span
                    class="situation-badge"
                    :class="vehicleSituationClass(row.agioPolinomial)"
                  >
                    {{ vehicleSituation(row.agioPolinomial) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section v-else-if="!isLoading" class="empty-state">
        <div class="empty-icon" aria-hidden="true">CSV</div>
        <h2>Nenhum resultado selecionado</h2>
        <p>Escolha um arquivo CSV e clique em Calcular para visualizar os dados.</p>
      </section>

      <section v-if="modelData" class="estimate-card" aria-labelledby="estimate-title">
        <div class="estimate-heading">
          <div>
            <p class="step-label">Estimativa final</p>
            <h2 id="estimate-title">Estime o preço do seu veículo</h2>
          </div>
          <span class="source-name">{{ selectedName }}</span>
        </div>

        <div class="estimate-content">
          <div class="estimate-form">
            <label class="estimate-field" for="estimate-year">
              <span>Ano do veículo</span>
              <input
                id="estimate-year"
                v-model="estimateYear"
                type="number"
                min="1886"
                placeholder="Ex.: 2022"
              >
            </label>

            <label class="estimate-field" for="estimate-km">
              <span>Quilometragem</span>
              <input
                id="estimate-km"
                v-model="estimateKm"
                type="number"
                min="0"
                step="1000"
                placeholder="Ex.: 48000"
              >
            </label>

            <button
              type="button"
              class="estimate-button"
              :disabled="isEstimating || !estimateYear || !estimateKm"
              @click="estimateVehiclePrice"
            >
              {{ isEstimating ? 'Estimando...' : 'Estimar preço' }}
            </button>
          </div>

          <div v-if="estimateResult" class="estimate-result">
            <article>
              <span>Modelo polinomial grau {{ estimateResult.degree }}</span>
              <strong>{{ formatCurrency(estimateResult.polynomial) }}</strong>
            </article>

            <button
              type="button"
              class="compare-button"
              @click="addEstimateToComparison"
            >
              <span aria-hidden="true">+</span>
              Adicionar à comparação
            </button>
          </div>

          <div v-if="estimateComparisons.length" class="comparisons">
            <div class="comparisons-heading">
              <h3>Estimativas adicionadas</h3>
              <span>{{ estimateComparisons.length }} {{ estimateComparisons.length === 1 ? 'veículo' : 'veículos' }}</span>
            </div>
            <div class="comparison-list">
              <article
                v-for="(estimate, index) in estimateComparisons"
                :key="estimate.id"
                class="comparison-item"
              >
                <div class="comparison-data">
                  <strong>{{ estimate.ano }} · {{ formatKm(estimate.km) }}</strong>
                  <span>
                    Grau {{ estimate.degree }} · {{ formatCurrency(estimate.polynomial) }}
                  </span>
                </div>
                <button
                  type="button"
                  class="remove-comparison"
                  :aria-label="`Remover estimativa ${index + 1}`"
                  @click="removeEstimate(index)"
                >
                  ×
                </button>
              </article>
            </div>
          </div>
        </div>
      </section>
    </section>
  </main>
</template>
