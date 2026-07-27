/**
 * Bundled test decals. Both are self-created project-original SVG assets
 * (see the licence comment inside each file) — no external downloads.
 */
export interface Decal {
  id: string
  label: string
  url: string
}

export const DECALS: Decal[] = [
  {
    id: 'orientation-test',
    label: 'Orientation test',
    url: '/decals/orientation-test.svg',
  },
  {
    id: 'geometric',
    label: 'Geometric',
    url: '/decals/geometric.svg',
  },
]
