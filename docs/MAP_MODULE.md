# Map and Geotagging Module

An isolated add-on: a citizen map at `/map` and an officials' risk map with
geotagging at `/admin/map`. It uses Leaflet 1.9 and OpenStreetMap tiles (free,
no API key). Everything lives in new files. Existing files receive only the
short pasted lines listed below.

## 1. New files (copy these into the project, same paths)

```
frontend/src/features/map/index.ts          barrel export
frontend/src/features/map/mapConfig.ts      tiles, India bounds, colour scales
frontend/src/features/map/mapData.ts        pagination helper, types
frontend/src/features/map/mapText.ts        English + Hindi strings (typed)
frontend/src/features/map/LeafletMap.tsx    React wrapper around Leaflet
frontend/src/features/map/MapLegend.tsx     colour key
frontend/src/features/map/GeotagPanel.tsx   GPS / pick-on-map / typed geotag editor
frontend/src/features/map/MapNavLabel.tsx   bilingual nav label + icon
frontend/src/pages/PublicMapPage.tsx        citizen map (status colours)
frontend/src/pages/admin/AdminMapPage.tsx   officials' map (risk colours + geotag)
backend/tests/test_geotag_schema.py         guards the geotag save contract
docs/MAP_MODULE.md                          this file
```

## 2. Install the library (run inside `frontend/`)

```
npm install leaflet@1.9.4
npm install -D @types/leaflet@^1.9
```

Pin 1.9.4. Leaflet 2.x is a different API.

## 3. Lines to paste into existing files

### frontend/src/routes/index.tsx

Below the last `import` line:

```tsx
import { PublicMapPage } from '@/pages/PublicMapPage'
import { AdminMapPage } from '@/pages/admin/AdminMapPage'
```

In the citizen block, below `<Route path="/about" ... />`:

```tsx
        <Route path="/map" element={<PublicMapPage />} />
```

In the officials' block, below `<Route path="/admin/analytics" ... />`:

```tsx
        <Route path="/admin/map" element={<AdminMapPage />} />
```

### frontend/src/layouts/PublicLayout.tsx

Below `import { Emblem } from '@/components/layout/Emblem'`:

```tsx
import { MapNavLabel } from '@/features/map'
```

Inside `navItems`, below the `/statistics` line:

```tsx
    { to: '/map', label: <MapNavLabel />, end: false },
```

### frontend/src/layouts/AdminLayout.tsx

Below `import { Emblem } from '@/components/layout/Emblem'`:

```tsx
import { MapNavIcon, MapNavLabel } from '@/features/map'
```

Inside `items`, below the `/admin/analytics` line:

```tsx
    { to: '/admin/map', label: <MapNavLabel />, icon: MapNavIcon, end: false },
```

### backend/app/schemas/project.py (required for saving geotags)

Inside `class ProjectUpdate`, directly below its `location: Optional[str] = None`
line (be sure it is the one in `ProjectUpdate`, not `ProjectCreate`):

```python
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
```

Without these two lines the PATCH request returns 200 but Pydantic silently
drops the coordinates, so nothing is saved. `test_geotag_schema.py` catches this.

## 4. Verify

```
cd frontend && npm run build
cd backend  && python -m tests.test_geotag_schema
cd backend  && python -m tests.run_all
```

Then check by hand: `/map` as a citizen, `/admin/map` as an officer, switch to
Hindi, select a work, click "Pick on map", click the map, save, and confirm the
marker moved and the Activity page shows "Project record updated (latitude, longitude)".

## 5. Behaviour notes

- **Separation kept:** the citizen map uses only the public API (status and
  public indicator). Risk levels appear only on `/admin/map`.
- **GPS** needs HTTPS or localhost (browser rule). Render is HTTPS, so it works
  on a phone at a site.
- **Offline:** if tiles cannot load, a banner appears; markers still render.
- **Accessibility:** each map has a "View as list" table, colour is paired with
  size and text labels, and popups are built with `textContent` (no HTML
  injection from work titles).
- **Sample data:** seeded coordinates are jittered around district
  headquarters, and the page says so.

## 6. Removing the module

Delete the files in section 1, remove the pasted lines in section 3, and run
`npm uninstall leaflet @types/leaflet`. The two backend lines are harmless
to keep.

## 7. Per-project location (added later)

New files: `features/map/ProjectLocationCard.tsx` (citizen) and
`features/map/ProjectLocationPanel.tsx` (officials). `LeafletMap.tsx`,
`mapText.ts`, `mapConfig.ts` and `index.ts` were updated, so replace the whole
`features/map` folder.

### frontend/src/pages/SchemeDetailPage.tsx (citizen)

Below `import { Card, CardBody, CardHeader } from '@/components/ui/Card'`:

```tsx
import { ProjectLocationCard } from '@/features/map'
```

Directly after the `<UtilizationDonut ... />` block in the right-hand column:

```tsx
          <ProjectLocationCard project={p} />
```

### frontend/src/pages/admin/AdminSchemeDetailPage.tsx (officials)

1. Below `import { RiskPanel } from '@/features/risk/RiskPanel'`:
   ```tsx
   import { MapNavIcon, ProjectLocationPanel, useMapText } from '@/features/map'
   ```
2. Below `const reload = () => setVersion((value) => value + 1)`:
   ```tsx
     const tm = useMapText()
   ```
3. In the `tabs` list, below the `progress` line:
   ```tsx
       { id: 'location', label: tm('locationTab'), icon: <MapNavIcon className="h-4 w-4" aria-hidden /> },
   ```
4. Below the `progress` `</TabPanel>`:
   ```tsx
           <TabPanel id="location" active={tab}>
             <ProjectLocationPanel project={p} canEdit={isReviewer} onSaved={reload} />
           </TabPanel>
   ```
