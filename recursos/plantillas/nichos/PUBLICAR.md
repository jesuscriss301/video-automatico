# Publicar los 7 mini videos por nicho

21 videos verticales (1080x1920, 35–39 s, en inglés, voz Heart). Cada nicho tiene 3 versiones, una por gancho (A, B y C), para probar cuál retiene más.
Archivos: `renders/<nicho>_<gancho>.mp4`.

| # | Nicho | Archivos | Título (YouTube Shorts) | Comentario fijado |
|---|---|---|---|---|
| 1 | Med spa | `medspa_a/b/c.mp4` | Injectables Website Design That Books Consultations (Med Spa Example) | Injectables website design example + booking & rebooking reminders → easyprodigital.com/blog/aesthetics-clinic-website-consultations · WhatsApp: wa.me/573238816434 |
| 2 | Albañiles | `masons_a/b/c.mp4` | Masonry Contractor Website + Hosting: What You Actually Need | Masonry contractor website + hosting example → demos.easyprodigital.com/masons · WhatsApp: wa.me/573238816434 |
| 3 | Taller mecánico | `autoshop_a/b/c.mp4` | Affordable Auto Shop Website Design That Books Appointments | Affordable auto shop website design → easyprodigital.com/blog/auto-shop-website-books-appointments · WhatsApp: wa.me/573238816434 |
| 4 | Bodegas | `storage_a/b/c.mp4` | Cheap Web Design for Self Storage That Fills Units | Self storage website + online rentals → easyprodigital.com/blog/self-storage-website-online-reservations · WhatsApp: wa.me/573238816434 |
| 5 | Plomeros | `plumbers_a/b/c.mp4` | Website Design for Plumbers in Independence: Get the 2 AM Calls | Website design for plumbers (Independence) + drain cleaning page example → easyprodigital.com/blog/plumbing-website-no-calls · WhatsApp: wa.me/573238816434 |
| 6 | Dentistas | `dentists_a/b/c.mp4` | Responsive Prosthodontic Websites: Implants, Dentures & Online Booking | Responsive prosthodontic website example + dental CRM → easyprodigital.com/blog/dental-website-new-patients · WhatsApp: wa.me/573238816434 |
| 7 | Car wash | `carwash_a/b/c.mp4` | Car Wash Website Design in Texas That Sells Memberships | Car wash website design (Texas) + memberships example → demos.easyprodigital.com/car-wash · WhatsApp: wa.me/573238816434 |

## Qué dice cada gancho

| Nicho | A | B | C |
|---|---|---|---|
| Med spa | Clients research for weeks… | What injectables website design should look like in 2026 | Botox clients come back… does your website remind them? |
| Albañiles | Your website is down and you don't know it | What it should include, in 40 seconds | Stop sending estimates by text |
| Taller mecánico | Your shop is full and your phone still rings | What $450 actually gets you | Customers don't trust mechanics they can't see online |
| Bodegas | Empty units cost you money every day | Cheap web design, built to rent units online | Customers don't know what unit size they need |
| Plomeros | 2 a.m., burst pipe… | Website design for plumbers in Independence | Reply in 5 minutes and win the job |
| Dentistas | One implant case can pay for your whole website | What patients check on their phone | Every missed appointment is money lost |
| Car wash | They sell memberships | Texas edition: what actually makes money | Rainy week? Members still pay |

## Antes de publicar

- **Bodegas:** la demo solo existe en español. El video la muestra tal cual, con narración en inglés. Si lo vas a publicar para EE. UU., crea la versión en inglés de la demo y vuelve a capturarla (a `build.py` solo hay que darle la imagen nueva).
- **Plomeros:** el título y el video dicen "Independence" sin el estado. Confirma en Search Console que es Independence, MO antes de agregarlo al título.
- **Maquetas del software** ("HOW IT WORKS"): son pantallas ilustrativas de cómo funcionaría el sistema, no un producto terminado. Si un cliente lo pide, se construye a medida.
- **Precios:** "$450" (taller), "$39/mo" (car wash) y "From $99" (plomeros) salen de tu página de precios o de las demos. Ajústalos si cambian.

## Cómo regenerar

```bash
python estudio/nichos/build.py --solo medspa_a --render   # uno
python estudio/nichos/build.py --render                   # los 21
```
Capturas: `estudio/nichos/capturas/` (Edge sin ventana, en inglés, 480 px de ancho en celular).
Voz: `scripts/narrar.py estudio/nichos/guiones/<nicho>.json --salida estudio/nichos/voz/<nicho>` con "Heart pausada (Kokoro, inglés)".
