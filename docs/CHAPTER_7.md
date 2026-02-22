# CHAPTER 7: Relational Fields

## Tujuan
Menambahkan relasi antar model menggunakan field Many2one, One2many, dan Many2many pada modul Estate.

## ⚠️ PENTING: Cara Melihat Perubahan

Setelah implementasi Chapter 7, Anda **HARUS** melakukan langkah berikut:

### 1. Upgrade Module
Buka Odoo → Apps → Klik filter "Installed" → Cari "Estate" → Klik **Upgrade**

Atau via terminal:
```bash
python odoo-bin -u estate -d nama_database
```

### 2. Refresh Browser
Tekan `Ctrl + F5` untuk clear cache dan reload halaman.

### 3. ⚠️ PENTING: Jika Field Masih NULL
Jika setelah upgrade Anda masih melihat `property_type_id` NULL di database, artinya **data lama belum terhapus**. Solusinya:

**Cara 1: Uninstall & Reinstall (RECOMMENDED)**
```
Odoo → Apps → Estate → Uninstall → Install lagi
```
Ini akan menghapus semua data lama dan membuat data demo baru yang lengkap.

**Cara 2: Manual Update via UI**
- Buka setiap property
- Pilih Property Type dari dropdown
- Tambahkan Tags
- Save

### 4. Cek Perubahan
- Buka menu **Estate → Properties**
- Sekarang hanya ada **5 properties** (tidak 10 lagi)
- Lihat kolom baru: **Property Type** dan **Tags** (dengan badge warna)
- Buka salah satu property
- Lihat **Tags** di header (colorful badges)
- Buka tab **Offers** untuk melihat daftar penawaran
- Buka tab **Other Info** untuk melihat Salesperson dan Buyer
- Property yang **Sold** atau **Offer Accepted** sudah ada Buyer dan Selling Price

## Model Baru yang Dibuat

### 1. Estate Property Type (`estate.property.type`)
Model untuk mengelola tipe properti.
- **File**: `models/estate_property_type.py`
- **Field**: `name` (Char, required)
- **Fungsi**: Mengkategorikan properti berdasarkan tipe (misalnya: Rumah, Apartemen, Tanah).

### 2. Estate Property Offer (`estate.property.offer`)
Model untuk mengelola penawaran terhadap properti.
- **File**: `models/estate_property_offer.py`
- **Fields**:
  - `price` (Float): Harga penawaran
  - `status` (Selection): Status penawaran (Accepted/Refused), tidak di-copy
  - `partner_id` (Many2one → res.partner, required): Partner yang membuat penawaran
  - `property_id` (Many2one → estate.property, required): Properti yang ditawarkan

### 3. Estate Property Tag (`estate.property.tag`)
Model untuk menambahkan label/tag pada properti.
- **File**: `models/estate_property_tag.py`
- **Field**: `name` (Char, required)
- **Fungsi**: Memberikan tag seperti "Cozy", "Renovated", "In City Center".

## Relational Fields di Estate Property

Model `estate.property` diperluas dengan field relasional:

### Many2one Fields
```python
property_type_id = fields.Many2one('estate.property.type', string='Property Type')
buyer_id = fields.Many2one('res.partner', string='Buyer', copy=False)
salesperson_id = fields.Many2one('res.users', string='Salesperson', default=lambda self: self.env.user)
```

- **property_type_id**: Menghubungkan properti dengan tipe properti
- **buyer_id**: Partner yang membeli properti (tidak di-copy saat duplikasi)
- **salesperson_id**: User yang menjadi salesperson (default: user saat ini)

### One2many Field
```python
offer_ids = fields.One2many('estate.property.offer', 'property_id', string='Offers')
```
- Menampilkan semua penawaran yang dibuat untuk properti ini

### Many2many Field
```python
tag_ids = fields.Many2many('estate.property.tag', string='Tags')
```
- Properti dapat memiliki banyak tag, dan satu tag bisa digunakan di banyak properti

## Konsep Penting

### Kenapa Perlu Upgrade Module?
Ketika Anda menambahkan **model baru** atau **field baru** ke model yang sudah ada:
- Odoo perlu membuat tabel database baru (untuk model baru)
- Odoo perlu menambahkan kolom baru di tabel database (untuk field baru)
- Views baru perlu diregister ke dalam database
- Menu baru perlu ditambahkan ke dalam database

Semua ini dilakukan saat **upgrade module**. Tanpa upgrade, Odoo masih membaca struktur lama.

### Syntax Many2many di XML
```xml
<field name="tag_ids" eval="[(6, 0, [ref('property_tag_luxury'), ref('property_tag_pool')])]"/>
```
- `(6, 0, [ids])`: Command untuk "set" relasi many2many
- `ref('property_tag_luxury')`: Mengambil ID record berdasarkan external ID

### Penjelasan Field NULL di Database

Ketika melihat data di database, Anda mungkin menemukan beberapa field NULL:

#### ✅ NORMAL (Field yang Boleh NULL):
- **`selling_price`**: NULL untuk property yang belum sold. Hanya terisi saat status = sold
- **`buyer_id`**: NULL untuk property yang belum ada buyer. Hanya terisi saat ada offer accepted/sold

#### ❌ TIDAK NORMAL (Field yang Seharusnya Terisi):
- **`property_type_id`**: Jika NULL, berarti data demo lama belum terhapus. Solusi: Uninstall & Reinstall module
- **`salesperson_id`**: Seharusnya default ke user yang login (admin)

#### Distribusi Data Demo (5 Properties):
1. **Luxury Villa** - Status: New (tidak ada offers)
2. **Modern City Apartment** - Status: Offer Received (2 offers pending)
3. **Spacious Family House** - Status: Offer Accepted (buyer: base.res_partner_2, selling_price: 325000)
4. **Beachfront Condo** - Status: Sold (buyer: base.res_partner_3, selling_price: 280000)
5. **Renovated Downtown Loft** - Status: New (tidak ada offers)

## Perubahan Views

### Form View Estate Property
Struktur baru dengan 3 tab:
1. **Description**: Deskripsi properti (sudah ada sebelumnya)
2. **Offers**: Menampilkan daftar penawaran dalam bentuk list inline
   - Field: price, partner_id, status
3. **Other Info**: Informasi tambahan
   - Field: salesperson_id, buyer_id

Tags ditampilkan di header menggunakan widget `many2many_tags`.

### Tree View Estate Property
Ditambahkan kolom:
- `property_type_id`
- `tag_ids` dengan widget `many2many_tags`

### Search View Estate Property
Ditambahkan field `property_type_id` untuk pencarian.

## Menu & Security

### Menu Baru
Settings submenu dengan 2 item:
- **Property Types**: Mengelola tipe properti
- **Property Tags**: Mengelola tag properti

### Security
Ditambahkan access rights untuk semua model baru:
- Full access (Read, Write, Create, Delete): `base.group_user` (semua internal user)

**Note Penting tentang Access Rights:**
- Untuk **development/learning**, semua user diberi full access agar mudah testing
- Untuk **production**, sebaiknya gunakan sistem group:
  - `base.group_user`: Read only
  - `estate.estate_admin`: Full access
  - Assign user ke group sesuai kebutuhan melalui Settings → Users → Access Rights

## Widget Khusus

### many2many_tags
Widget yang digunakan untuk menampilkan many2many field sebagai tag badges yang elegan:
```xml
<field name="tag_ids" widget="many2many_tags"/>
```

## Ringkasan Implementasi

1. **3 model baru**: Property Type, Property Offer, Property Tag
2. **5 relational fields baru** di Estate Property:
   - `property_type_id` (Many2one)
   - `buyer_id` (Many2one, copy=False)
   - `salesperson_id` (Many2one, default=current user)
   - `tag_ids` (Many2many)
   - `offer_ids` (One2many)
3. **Views**: Tree, Form untuk semua model baru
4. **Menu Settings** untuk konfigurasi master data
5. **Security access** untuk kontrol akses
6. **Widget tags** untuk tampilan yang lebih baik
7. **Data demo lengkap** dengan 5 properties yang mencakup berbagai status dan relasi

## Troubleshooting

### Problem: Field property_type_id, buyer_id, dll masih NULL
**Penyebab**: Data lama dari Chapter sebelumnya belum terhapus, sementara demo.xml sudah berubah.

**Solusi**:
1. Uninstall module Estate
2. Install ulang module Estate
3. Demo data akan terbuat ulang dengan relasi yang benar

### Problem: Tags tidak muncul sebagai badges
**Penyebab**: Widget tidak diterapkan di view.

**Solusi**: Pastikan di view XML ada `widget="many2many_tags"` pada field tag_ids

### Problem: Tab Offers atau Other Info tidak muncul
**Penyebab**: Module belum di-upgrade.

**Solusi**: Upgrade module Estate dari menu Apps

## Data Demo

Data demo telah diupdate dengan:
- **4 Property Types**: Villa, Apartment, House, Condo
- **7 Property Tags**: Cozy, Renovated, Luxury, In City Center, Ocean View, With Pool, Modern
- **5 Property Offers**: Berbagai penawaran dari partners untuk property tertentu
- **5 Properties** dengan berbagai status:
  - 2 New (belum ada offers)
  - 1 Offer Received (sedang ada penawaran)
  - 1 Offer Accepted (offer diterima, ada buyer & selling price)
  - 1 Sold (sudah terjual, ada buyer & selling price)

**Perbedaan dengan data sebelumnya:**
- Jumlah property dikurangi dari 10 menjadi 5 untuk mempermudah testing
- Setiap property sudah terhubung dengan Type dan Tags
- Property yang sudah sold/offer_accepted sudah memiliki buyer_id dan selling_price
- Semua property memiliki salesperson_id (default: admin user)

Implementasi ini memungkinkan sistem Estate untuk mengelola relasi antar data dengan lebih terstruktur dan memudahkan user dalam mengorganisir informasi properti.
