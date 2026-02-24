# Chapter 8: Fields Computation

## Ringkasan
Implementasi computed fields, related fields, dan inverse functions pada modul Estate.

## 1. Computed Fields (estate.property)

### total_area
- **Tipe**: Integer (computed)
- **Rumus**: `living_area + garden_area`
- **Dependencies**: `living_area`, `garden_area`
- **Lokasi**: Tab Description di form view

### best_price
- **Tipe**: Float (computed)
- **Rumus**: Nilai maksimum dari semua harga offer
- **Dependencies**: `offer_ids.price`
- **Lokasi**: Form view di samping expected_price
- **Default**: 0.0 jika tidak ada offer

## 2. Related Field (estate.property.offer)

### property_type_id
- **Tipe**: Many2one (related)
- **Related ke**: `property_id.property_type_id`
- **Stored**: Ya
- **Tujuan**: Akses tipe properti langsung dari record offer
- **Visibilitas**: Ditambahkan ke offer tree view dan form view

## 3. Computed Field dengan Inverse (estate.property.offer)

### validity
- **Tipe**: Integer
- **Default**: 7 hari
- **Tujuan**: Jumlah hari hingga deadline offer

### date_deadline
- **Tipe**: Date (computed dengan inverse)
- **Rumus**: `create_date + validity` hari
- **Inverse**: Update `validity` ketika `date_deadline` diubah
- **Fallback**: Menggunakan tanggal hari ini jika `create_date` belum ada
- **Visibilitas**: Ditambahkan ke form view dan list view

## 4. Struktur Menu Baru

**Menu Advertisement** ditambahkan di bawah Estate dengan:
- **Offers**: Menampilkan semua property offers dengan kolom:
  - property_id
  - partner_id
  - price
  - validity
  - date_deadline
  - status
  - property_type_id

## Detail Implementasi Kunci

### Penggunaan Decorator
- `@api.depends()`: Mendeklarasikan dependencies field untuk computed fields
- `compute=`: Mendefinisikan method computation
- `inverse=`: Mendefinisikan method inverse untuk komputasi dua arah

### Pattern Compute Method
```python
@api.depends('field1', 'field2')
def _compute_target_field(self):
    for record in self:
        record.target_field = computation_logic
```

### Pattern Inverse Method
```python
def _inverse_target_field(self):
    for record in self:
        record.source_field = reverse_computation_logic
```

### Pattern Related Field
```python
field_name = fields.Many2one(
    'model.name',
    related='path.to.field',
    store=True
)
```

## File yang Dimodifikasi

1. **models/estate_property.py**: Menambahkan `total_area` dan `best_price` computed fields
2. **models/estate_property_offer.py**: Menambahkan `property_type_id` (related), `validity`, dan `date_deadline` (computed dengan inverse)
3. **views/estate_property_views.xml**: Update form view untuk menampilkan computed fields baru
4. **views/estate_property_offer_views.xml**: Update tree dan form views, menambahkan action
5. **views/estate_menu.xml**: Menambahkan menu Advertisement dengan submenu Offers

## Cara Testing di UI Odoo

### Persiapan
1. Restart Odoo server
2. Login ke Odoo
3. Update module Estate: Buka **Apps** → Cari "Estate" → Klik **Upgrade**

### Test 1: Computed Field `total_area`
1. Buka menu **Estate → Properties → Properties**
2. Buka salah satu property atau buat property baru
3. Klik tab **Description**
4. Isi nilai **Living Area (sqm)**: misalnya `100`
5. Centang checkbox **Garden**
6. Isi nilai **Garden Area**: misalnya `50`
7. Scroll ke bawah, lihat field **Total Area (sqm)** → Harus otomatis menampilkan `150` (100 + 50)
8. Ubah nilai Living Area atau Garden Area, perhatikan Total Area otomatis berubah

### Test 2: Computed Field `best_price`
1. Masih di form view Property
2. Lihat bagian atas form, ada field **Best Price** (di bawah Expected Price)
3. Awalnya Best Price menampilkan `0.00` (tidak ada offer)
4. Klik tab **Offers**
5. Klik **Add a line**, isi:
   - **Price**: `100000`
   - **Partner**: Pilih partner mana saja
   - Biarkan validity default 7
6. Klik **Save** (property)
7. Lihat field **Best Price** → Harus menampilkan `100,000.00`
8. Tambahkan offer lagi dengan price `150000`
9. Klik **Save**
10. Best Price harus berubah menjadi `150,000.00` (nilai tertinggi)

### Test 3: Related Field `property_type_id` di Offers
1. Buka menu **Estate → Advertisement → Offers**
2. Perhatikan kolom **Property Type** muncul di list view
3. Jika ada offer yang property-nya memiliki type, type-nya akan muncul di kolom ini
4. Untuk testing lebih lanjut:
   - Buat property baru dengan Property Type: "House"
   - Tambahkan offer ke property tersebut
   - Buka menu **Estate → Advertisement → Offers**
   - Lihat offer yang baru dibuat, kolom Property Type harus menampilkan "House"

### Test 4: Computed Field dengan Inverse (`date_deadline` dan `validity`)
**Test A - Compute dari Validity ke Date Deadline:**
1. Buka menu **Estate → Properties → Properties**
2. Buka sebuah property
3. Klik tab **Offers**
4. Klik **Add a line**:
   - **Price**: `200000`
   - **Partner**: Pilih partner
   - **Validity**: Isi `10` (hari)
5. Perhatikan field **Deadline** otomatis terisi dengan tanggal 10 hari dari sekarang
6. Ubah **Validity** menjadi `15`
7. **Deadline** harus otomatis berubah menjadi 15 hari dari sekarang

**Test B - Inverse dari Date Deadline ke Validity:**
1. Masih di offer yang sama atau buat offer baru
2. Klik pada field **Deadline**
3. Pilih tanggal 20 hari dari sekarang (misalnya jika hari ini 24 Feb 2026, pilih 16 Mar 2026)
4. Tab keluar dari field atau klik area lain
5. Perhatikan field **Validity** otomatis berubah menjadi `20`
6. Ini membuktikan inverse function bekerja (date_deadline → validity)

### Test 5: Form View Offers Standalone
1. Buka menu **Estate → Advertisement → Offers**
2. Klik **Create** untuk membuat offer baru
3. Isi form:
   - **Property**: Pilih property
   - **Partner**: Pilih partner
   - **Price**: `175000`
   - **Validity**: `14`
4. Perhatikan:
   - **Deadline** otomatis terisi
   - **Property Type** otomatis terisi sesuai property yang dipilih
5. Klik **Save**
6. Buka lagi offer tersebut
7. Ubah **Deadline** ke tanggal lain
8. **Validity** harus ikut berubah sesuai selisih hari

### Checklist Verifikasi
- ✅ Total Area = Living Area + Garden Area
- ✅ Best Price menampilkan harga offer tertinggi
- ✅ Property Type muncul di list Offers
- ✅ Date Deadline otomatis dihitung dari Validity
- ✅ Mengubah Date Deadline akan update Validity
- ✅ Mengubah Validity akan update Date Deadline
- ✅ Menu Advertisement dengan submenu Offers sudah muncul

### Troubleshooting
**Jika perubahan tidak muncul:**
1. Pastikan sudah restart Odoo server
2. Update module Estate di Apps
3. Clear cache browser (Ctrl + F5)
4. Jika masih tidak muncul, cek log Odoo untuk error
