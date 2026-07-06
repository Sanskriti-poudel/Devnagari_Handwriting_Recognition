export function downloadTextFile(text: string, filename: string) {
  const blob = new Blob(['﻿' + text], { type: 'text/plain;charset=utf-8' })
  triggerDownload(blob, filename)
}

/**
 * jsPDF's built-in fonts can't render Devanagari glyphs, so the text is first
 * rasterized off-screen (with the Noto Sans Devanagari font actually applied)
 * and the resulting image is embedded into the PDF page.
 */
export async function downloadTextAsPdf(text: string, filename: string) {
  const [{ default: jsPDF }, { default: html2canvas }] = await Promise.all([import('jspdf'), import('html2canvas')])

  const container = document.createElement('div')
  container.style.position = 'fixed'
  container.style.left = '-9999px'
  container.style.top = '0'
  container.style.width = '700px'
  container.style.padding = '32px'
  container.style.background = '#ffffff'
  container.style.color = '#0f172a'
  container.style.fontFamily = "'Noto Sans Devanagari', 'Inter', sans-serif"
  container.style.fontSize = '18px'
  container.style.lineHeight = '2'
  container.style.whiteSpace = 'pre-wrap'
  container.style.wordBreak = 'break-word'
  container.textContent = text || ' '
  document.body.appendChild(container)

  try {
    const canvas = await html2canvas(container, { scale: 2, backgroundColor: '#ffffff' })
    const imgData = canvas.toDataURL('image/png')

    const pdf = new jsPDF({ unit: 'pt', format: 'a4' })
    const pageWidth = pdf.internal.pageSize.getWidth()
    const pageHeight = pdf.internal.pageSize.getHeight()
    const imgWidth = pageWidth - 48
    const imgHeight = (canvas.height * imgWidth) / canvas.width

    let heightLeft = imgHeight
    let position = 24

    pdf.addImage(imgData, 'PNG', 24, position, imgWidth, imgHeight)
    heightLeft -= pageHeight

    while (heightLeft > 0) {
      position = heightLeft - imgHeight + 24
      pdf.addPage()
      pdf.addImage(imgData, 'PNG', 24, position, imgWidth, imgHeight)
      heightLeft -= pageHeight
    }

    pdf.save(filename)
  } finally {
    document.body.removeChild(container)
  }
}

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
