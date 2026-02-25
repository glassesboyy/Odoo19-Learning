# Chapter 10: Actions

## Ringkasan
Implementasi action methods untuk tombol Cancel, Sold, Accept, dan Refuse dengan validasi business logic.

## Exercise 1: Tombol Cancel dan Sold
**Lokasi**: `custom_addons/estate/models/estate_property.py` dan `custom_addons/estate/views/estate_property_views.xml`

### Model - Action Methods:
```python
def action_cancel(self):
    for record in self:
        if record.state == 'sold':
            raise UserError("Sold property cannot be canceled.")
        record.state = 'canceled'

def action_sold(self):
    for record in self:
        if record.state == 'canceled':
            raise UserError("Canceled property cannot be sold.")
        record.state = 'sold'
```

### View - Header Buttons:
```xml
<header>
    <button name="action_sold" type="object" string="Sold"/>
    <button name="action_cancel" type="object" string="Cancel"/>
</header>
```

**Logika**:
- Property yang sudah Sold tidak bisa di-Cancel
- Property yang sudah Canceled tidak bisa di-Sold
- Menggunakan `UserError` untuk menampilkan pesan error

## Exercise 2: Tombol Accept dan Refuse
**Lokasi**: `custom_addons/estate/models/estate_property_offer.py` dan `custom_addons/estate/views/estate_property_views.xml`

### Model - Action Methods:
```python
def action_accept(self):
    for record in self:
        # Check if another offer is already accepted
        if record.property_id.offer_ids.filtered(lambda o: o.status == 'accepted' and o.id != record.id):
            raise UserError("Another offer has already been accepted for this property.")
        record.status = 'accepted'
        # Set buyer and selling price on property
        record.property_id.buyer_id = record.partner_id
        record.property_id.selling_price = record.price

def action_refuse(self):
    for record in self:
        record.status = 'refused'
```

### View - Icon Buttons di List:
```xml
<field name="offer_ids">
    <list>
        <field name="price"/>
        <field name="partner_id"/>
        <field name="validity"/>
        <field name="date_deadline"/>
        <field name="status"/>
        <button name="action_accept" type="object" icon="fa-check"/>
        <button name="action_refuse" type="object" icon="fa-times"/>
    </list>
</field>
```

**Logika**:
- Ketika offer di-Accept:
  - Set `buyer_id` property dengan partner dari offer
  - Set `selling_price` property dengan price dari offer
  - Validasi: hanya 1 offer yang bisa accepted per property
- Ketika offer di-Refuse:
  - Set status menjadi 'refused'
- Menggunakan icon FontAwesome: `fa-check` (✓) dan `fa-times` (✗)

## Konsep Penting
- **Action Methods**: Method yang dipanggil dari button UI
- **UserError**: Exception untuk menampilkan pesan error ke user
- **Button Types**: `type="object"` untuk memanggil Python method
- **Icon Buttons**: Gunakan atribut `icon` dengan FontAwesome class
- **Business Logic Validation**: Pastikan state transitions valid

## Testing
1. Buat property dan coba tekan Cancel, lalu coba Sold → harus error
2. Buat property dan coba tekan Sold, lalu coba Cancel → harus error
3. Buat beberapa offer untuk property, Accept satu offer → buyer dan selling price terisi
4. Coba Accept offer lain → harus error (sudah ada yang accepted)
5. Refuse offer → status berubah jadi refused
