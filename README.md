# m: Meridian Motors

A website for a used-car dealership, written in plain HTML, CSS and JavaScript. There's no build step and nothing to install.

It has:

- **Inventory** with live search, filters (body type, make, max price), sorting and a "Saved" list. Visitors save cars by tapping the heart, and the list is remembered in their browser.
- **Vehicle details** in a pop-up with photos, specs, highlights, an estimated monthly payment, and buttons that book a test drive or open the payment calculator with that car's price.
- **Quick search** in the hero, which shows how many cars match before the visitor searches.
- **Payment calculator** for price, down payment, trade-in, APR and term, showing the monthly payment, total interest and total cost.
- **Trade-in section**, plus a contact and test-drive form that can be pre-filled from any car.
- **Showroom hours** with a live "Open now / Closed now" label and today's row highlighted.
- A responsive layout with a mobile menu, an automatic dark mode, and accessibility basics: a skip link, labelled controls and a keyboard-friendly dialog.

## Structure

```
index.html              Page layout and all fixed text (dealer name, address, hours, perks…)
assets/js/inventory.js  Your cars, plus currency, units and finance defaults: edit this most often
assets/js/main.js       Filters, dialog, calculator, form and hours logic
assets/css/style.css    Styles. Colors and fonts are tokens at the top
assets/img/             Hero image, trade-in background and car photos (cars/)
```

## Make it yours

### 1. Your cars

Open `assets/js/inventory.js`. Each car is one object in `window.INVENTORY`:

```js
{
  id: 'toyota-rav4',               // unique, used in links and the saved list
  stock: 'M1046',
  year: 2021, make: 'Toyota', model: 'RAV4', trim: 'Adventure AWD',
  body: 'SUV',                     // SUV, Sedan, Truck, Coupe, Hatchback, Convertible, Wagon, Van…
  price: 30900, wasPrice: 32900,   // wasPrice is optional and shows as a struck-through price
  mileage: 28400,
  fuel: 'Gas', transmission: 'Automatic', drivetrain: 'AWD',
  engine: '2.5L 4-cylinder, 203 hp', economy: '25 city / 32 hwy mpg',
  exterior: 'Cavalry Blue', interior: 'Black SofTex',
  badge: 'Popular',                // optional: 'Just arrived', 'Price drop', 'Electric', anything
  image: 'assets/img/cars/toyota-rav4.jpg',
  alt: 'Blue Toyota RAV4 parked by a house',
  features: ['Heated seats', 'Power liftgate'],
  description: 'One local owner…',
}
```

The filters, makes list, counts and contact-form vehicle list all build themselves from this data. Body-type filter chips only appear for body types you actually have.

**Photos:** use 3:2 landscape images at about 1200×800 and put them in `assets/img/cars/`. The sample photos are placeholders, so replace them with photos of your real cars.

### 2. Dealership details

In `index.html`, search for and replace:

- `Meridian Motors` / `Meridian` with your name
- `1200 Meridian Avenue`, `Springfield` and `ST 00000` with your address (also update the "Get directions" link)
- `(312) 555-0142` and `+13125550142` with your phone number
- `sales@example.com` with your email (also set `email` in `inventory.js`)

**Hours:** edit the table in the "Visit us" section. The `data-open` and `data-close` times are 24-hour (`"09:00"`, `"19:00"`), and a day with neither is treated as closed. The open/closed label uses the visitor's local time.

**Perks and copy:** the four perks under the hero (inspection, returns, history report, financing) are examples. Change them to the guarantees you actually offer.

### 3. Money, units and finance defaults

At the top of `assets/js/inventory.js`:

```js
locale: 'en-US', currency: 'USD', distanceUnit: 'mi',
finance: { apr: 6.9, termMonths: 72, downPaymentPct: 10 },
```

For example, `locale: 'en-GB', currency: 'GBP', distanceUnit: 'mi'` or `locale: 'de-DE', currency: 'EUR', distanceUnit: 'km'`. The finance values drive the "est. /mo" figure on every car and the calculator's starting values.

### 4. Colors and fonts

Edit the variables at the top of `assets/css/style.css`. `--btn` sets the main button color, `--accent` sets the link and icon color, and `--night` sets the dark header, hero and footer. Headings use Archivo and body text uses Inter, both from Google Fonts.

## The contact form

By default, **Send message** opens the visitor's email app with their message already written and addressed to you, so it works with no server.

To receive submissions directly instead, sign up for a form service such as [Formspree](https://formspree.io) or [Netlify Forms](https://docs.netlify.com/forms/setup/) and set the form's `action` in `index.html`:

```html
<form class="contact-form" id="contact-form" method="post" action="https://formspree.io/f/your-id" novalidate>
```

When an `action` is set, the form posts there normally after the same validation.

## Preview locally

```sh
python3 -m http.server 8000
# open http://localhost:8000
```

## Publish it

**GitHub Pages:** in the repo, go to **Settings → Pages**, set **Source** to *Deploy from a branch*, pick `main` and `/ (root)`, and save. The site will be published at `https://<username>.github.io/m/`.

Netlify, Vercel and Cloudflare Pages also work. The site is static, so you can point any of them at the repo with no build command.

## Sample content and photo credits

The listings (prices, mileage, stock numbers, descriptions), dealership name, address and phone number are made up for demonstration. The phone number is in the 555-01xx range reserved for fictional use.

The photos are from [Unsplash](https://unsplash.com/license) and are free to use under the Unsplash License:

| Image | Photographer |
| --- | --- |
| Hero (Ford Mustang) | [Ryan Spencer](https://unsplash.com/photos/white-sports-car-in-parking-garage-c-NEiPIxpYI) |
| Porsche 911 GT3 | [Laurent Perren](https://unsplash.com/photos/silver-porsche-911-on-road-during-daytime-NeH9w4CdmnA) |
| BMW M3 Competition | [Lorenzo Hamers](https://unsplash.com/photos/black-coupe-parked-in-a-building-9njClq6GPG0) |
| Tesla Model 3 | [Bram Van Oost](https://unsplash.com/photos/a-tesla-electric-car-charging-at-a-charging-station-W8IvFdsKsl8) |
| Ford Expedition | [Sven D](https://unsplash.com/photos/parked-white-ford-explorer-suv-a4S6KUuLeoM) |
| Jeep Wrangler | [Quilia](https://unsplash.com/photos/black-jeep-wrangler-yDekvyZ52dU) |
| Toyota Tacoma | [Dusty Barnes](https://unsplash.com/photos/tan-toyota-tacoma-pickup-truck-o7fqZ18YFXc) |
| Toyota RAV4 | [Stephen Andrews](https://unsplash.com/photos/a-blue-toyota-rav-parked-in-front-of-a-house-PNyyffLvWIs) |
| Volkswagen Golf GTI | [Autotrader UK](https://unsplash.com/photos/a-white-volkswagen-golf-drives-on-a-road-jLba2Etjp8A) |
| Chevrolet Camaro | [Jesse Collins](https://unsplash.com/photos/black-convertible-coupe-parked-near-high-rise-building-lrmo2hlFYE4) |
| Trade-in background (VW Golf R) | [Luke Miller](https://unsplash.com/photos/a-dark-grey-volkswagen-golf-parked-in-a-garage-yZ9_WcRVxMQ) |
