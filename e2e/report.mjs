// Merges per-step screenshots into pytest-bdd's Cucumber JSON and renders it as an HTML report.
import { existsSync, mkdirSync, rmSync, readFileSync, writeFileSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { generate } from 'multiple-cucumber-html-reporter'

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const reportDir = join(root, 'reports', 'e2e')
const screenshotDir = join(reportDir, 'screenshots')
const jsonPath = join(reportDir, 'cucumber.json')

if (!existsSync(jsonPath)) {
  console.error(`No Cucumber JSON at ${jsonPath}; run \`make e2e\` first.`)
  process.exit(1)
}

const index = existsSync(join(screenshotDir, 'index.json'))
  ? JSON.parse(readFileSync(join(screenshotDir, 'index.json'), 'utf8'))
  : {}

const features = JSON.parse(readFileSync(jsonPath, 'utf8'))
for (const feature of features) {
  for (const scenario of feature.elements) {
    const shots = index[`${feature.uri}::${scenario.name}`] ?? {}
    scenario.steps.forEach((step, i) => {
      const file = shots[String(i)]
      if (!file) return
      const data = readFileSync(join(screenshotDir, file)).toString('base64')
      step.embeddings = [{ data, mime_type: 'image/png' }]
    })
  }
}

const mergedDir = join(reportDir, 'merged')
mkdirSync(mergedDir, { recursive: true })
writeFileSync(join(mergedDir, 'cucumber.json'), JSON.stringify(features))

rmSync(join(reportDir, 'html'), { recursive: true, force: true })

generate({
  jsonDir: mergedDir,
  reportPath: join(reportDir, 'html'),
  displayDuration: true,
  pageTitle: 'Brownsea Intranet E2E',
  reportName: 'Brownsea Intranet E2E',
  useCDN: false,
})
