<script setup>
import { onMounted, ref } from 'vue'

const csvFiles = ref([])
const selectedCsv = ref('')
const rows = ref([])
const selectedName = ref('')
const isLoading = ref(false)
const isLoadingFiles = ref(true)
const errorMessage = ref('')
const normalizedData = ref(null)

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

async function calculateSelectedCsv() {
  if (!selectedCsv.value) return

  isLoading.value = true
  errorMessage.value = ''
  normalizedData.value = null

  try {
    const [dataResponse, normalizationResponse] = await Promise.all([
      fetch(`/api/dados/${encodeURIComponent(selectedCsv.value)}`),
      fetch(`/api/funcoes/normaliza/${encodeURIComponent(selectedCsv.value)}`),
    ])

    if (!dataResponse.ok) throw new Error(`HTTP ${dataResponse.status}`)
    if (!normalizationResponse.ok) throw new Error(`HTTP ${normalizationResponse.status}`)

    const data = await dataResponse.json()
    const normalizationData = await normalizationResponse.json()
    rows.value = data.rows ?? []
    selectedName.value = data.csv_file ?? selectedCsv.value
    normalizedData.value = normalizationData.normalized
  } catch (error) {
    rows.value = []
    normalizedData.value = null
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

          <button type="button" class="add-button" disabled>
            <span aria-hidden="true">+</span>
            Adicionar novo
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

      <details v-if="normalizedData" class="process-details">
        <summary>
          <span>
            <span class="process-step">Etapa intermediaria</span>
            <strong>Parte 1: Normalizando os dados</strong>
          </span>
          <span class="expand-label">Expandir</span>
        </summary>

        <div class="process-content">
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

        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th scope="col">Ano</th>
                <th scope="col">Quilometragem</th>
                <th scope="col">Preço</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, index) in rows" :key="`${row.ano}-${row.km}-${index}`">
                <td><span class="year-badge">{{ row.ano }}</span></td>
                <td>{{ formatKm(row.km) }}</td>
                <td class="price-cell">{{ formatCurrency(row.preco) }}</td>
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
    </section>
  </main>
</template>
