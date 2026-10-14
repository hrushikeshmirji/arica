export const FALLBACK_IMAGE_DATA_URI =
  "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='300' viewBox='0 0 400 300'%3E%3Crect width='400' height='300' fill='%231e293b'/%3E%3Cpath d='M200,60 C250,120 280,200 200,260 C120,200 150,120 200,60 Z' fill='%2310b981' opacity='0.7'/%3E%3Ctext x='200' y='280' font-family='sans-serif' font-size='14' fill='%2394a3b8' text-anchor='middle'%3EArecaVision AI%3C/text%3E%3C/svg%3E"

export const DISEASE_LOCAL_SAMPLE_MAP: Record<string, string> = {
  koleroga: "/samples/sample_koleroga.jpg",
  "fruit rot": "/samples/sample_koleroga.jpg",
  mahali: "/samples/sample_koleroga.jpg",
  anthracnose: "/samples/sample_anthracnose.jpg",
  "leaf spot": "/samples/sample_leaf_spot.jpg",
  leafspotcomplex: "/samples/sample_leaf_spot.jpg",
  "yellow leaf": "/samples/sample_yellow_leaf.jpg",
  "stem bleeding": "/samples/sample_stem_bleeding.jpg",
  "stem cracking": "/samples/sample_stem_cracking.jpg",
  "bud borer": "/samples/sample_bud_borer.jpg",
  "nut cracking": "/samples/sample_nut_cracking.jpg",
  "sooty mold": "/samples/sample_sooty_mold.jpg",
  phytoplasma: "/samples/sample_phytoplasma.jpg",
  "root wilt": "/samples/sample_phytoplasma.jpg",
  healthy: "/samples/sample_healthy.jpg",
}

export function getSampleImageForDisease(disease?: string, currentUrl?: string): string {
  if (currentUrl && !currentUrl.startsWith("blob:") && currentUrl.trim() !== "") {
    if (currentUrl.startsWith("/samples/")) {
      return currentUrl
    }
  }
  const query = (disease || "").toLowerCase()
  for (const [key, path] of Object.entries(DISEASE_LOCAL_SAMPLE_MAP)) {
    if (query.includes(key)) {
      return path
    }
  }
  return "/samples/sample_leaf_spot.jpg"
}

export function handleImageError(e: React.SyntheticEvent<HTMLImageElement>): void {
  const target = e.currentTarget
  if (target.src !== FALLBACK_IMAGE_DATA_URI) {
    target.src = FALLBACK_IMAGE_DATA_URI
  }
}
