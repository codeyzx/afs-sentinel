# Risk Analisis Overview
| Risk Category                                | Pertanyaan utama                                          | Contoh metode                                                                                                                                |
| -------------------------------------------- | --------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| **1. Financial Distress Risk**               | Apakah perusahaan berisiko mengalami kesulitan finansial? | Altman Z-Score, liquidity, leverage                                                                                                          |
| **2. Earnings Quality Risk**                 | Seberapa berkualitas dan sustainable laba perusahaan?     | Sloan, persistence, accruals, cash conversion, YoY Cash vs Earnings Divergence (supporting), DSO Spike (Days Sales Outstanding) (supporting) |
| **3. Financial Statement Manipulation Risk** | Apakah ada indikasi manipulasi/salah saji?                | **Beneish M-Score, Dechow F-Score**                                                                                                          |
| **4. Market Risk**                           | Seberapa besar risiko dari pergerakan pasar?              | Beta, volatility, drawdown                                                                                                                   |
| **5. Business / Operational Risk**           | Seberapa rentan fundamental bisnis?                       | Revenue concentration, margin volatility, segment risk                                                                                       |
| **6. Governance / Management Risk**          | Apakah ada red flags dari manajemen/governance?           | Insider selling, RPT, ownership, auditor/restatement                                                                                         |
jika di urutkan mana yang paling penting dalam perspektif scope laporan keuangan
1. **Fundamental Risk**
	1. Financial Distress
	2. Earnings Quality
	3. Financial Statement Manipulation

2. **Company-specific Risk**  
	1. Business/Operational  
	2. Governance/Management

3. **Market Risk**  
	1. Market/Systematic Risk (fokusnya itu relasi emiten dengan pasar keseluruuhan )

# Financial Distress (kesulitan keuangan)
## Altman Z-Score
Dalam berbagai studi akademik, **Altman Z-score** (**_bankruptcy model_**) dipergunakan sebagai alat kontrol terukur terhadap status keuangan suatu perusahaan yang sedang mengalami kesulitan keuangan (_financial distress_). Dengan kata lain, **Altman Z-score** dipergunakan sebagai alat untuk memprediksi kebangkrutan suatu perusahaan.

Altman Z-score dinyatakan dalam bentuk persamaan linear yang terdiri dari 4 hingga 5 koefisien “T” yang mewakili rasio-rasio keuangan tertentu, yakni:
```
Z = 1,2 T1 + 1,4 T2 + 3,3 T3 + 0,6 T4 + 0,99 T5

Di mana:

T1 = modal kerja neto / total aset

T2 = saldo laba / total aset

T3 = EBIT / total aset

T4 = nilai pasar terhadap ekuitas / nilai buku terhadap total liabilitas

T5 = penjualan / total aset

Dengan zona diskriminan sebagai berikut:

Bila Z > 2.99 = zona “aman”

Bila 1.81 < Z < 2.99 = zona “abu-abu”

Bila Z < 1.81 = zona “_distress_”
```

Namun, Z-score tidak dipergunakan untuk perusahaan jenis jasa keuangan atau lembaga keuangan, baik swasta maupun pemerintah.. Hal ini karena adanya kecenderungan perbedaan yang cukup besar antara neraca suatu institusi keuangan dengan institusi keuangan lainnya.

Saat ini, formula Z-score untuk perusahaan jenis manufaktur dan non-manufaktur dibedakan sebagai berikut:

1. Untuk perusahaan manufaktur, menggunakan formula yang terdiri dari 5 koefisien, yakni:
```
Z = 0,717 T1 + 0,847 T2 + 3,107 T3 + 0,420 T4 + 0,998 T5

Dengan zona diskiriman sbb:

Bila Z > 2,9 = zona “aman”

Bila 1,23 < Z < 2,9 = zona “abu-abu”

Bila Z < 1,23 = zona “_distress_”
```

2. Untuk perusahaan non-manufaktur, menggunakan formula yang terdiri dari 4 koefisien, yakni:
```


Z = 6,56 T1 + 3,26 T2 + 6,72 T3 + 1,05 T4

Dengan zona diskriminan sebagai berikut:

Bila Z > 2,9 = zona “aman”

Bila 1,22 < Z < 2,9 = zona “abu-abu”

Bila Z < 1,22 = zona “_distress_”

```
### Status API

| **Komponen Altman Z-Score**                  | **Status Ketersediaan** | Endpoint                                                                            | **Formula / Metrik**                                                                                                                                                |
| -------------------------------------------- | ----------------------- | ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **$X_1$** (Working Capital / Total Assets)   | Tersedia                | `GET /v2/financials/quarterly/{symbol}/`                                            | `(total_current_asset - current_liabilities) / total_assets`                                                                                                        |
| **$X_2$** (Retained Earnings / Total Assets) | Tidak Eksplisit         | `GET /v2/financials/quarterly/{symbol}/`                                            | _Field_ spesifik Saldo Laba (Retained Earnings) tidak ada di contoh respons; Anda perlu memverifikasi ketersediaannya atau menggunakan turunan dari `total_equity`. |
| **$X_3$** (EBIT / Total Assets)              | Tersedia                | `GET /v2/financials/quarterly/{symbol}/`                                            | `ebit / total_assets`                                                                                                                                               |
| **$X_4$** (Market Value / Total Liabilities) | Tersedia                | `GET /v2/daily/{symbol}/`<br><br>  <br><br>`GET /v2/financials/quarterly/{symbol}/` | Membutuhkan _join_ antara Market Cap (dari data `/v2/daily/`) dibagi dengan `total_liabilities` (dari `/v2/financials/quarterly/`).                                 |
| **$X_5$** (Sales / Total Assets)             | Tersedia                | `GET /v2/financials/quarterly/{symbol}/`                                            | `revenue / total_assets`                                                                                                                                            |

https://accounting.binus.ac.id/2015/03/09/altman-z-score-model-untuk-memprediksi-kesulitan-keuangan-perusahaan/
# Earning Quality
## Sloan Method

$$Sloan\ Accrual\ Ratio = \frac{Net\ Income - Operating\ Cash\ Flow}{Average\ Total\ Assets}$$

Jika hasilnya lebih dari **+10% (0.1)**, itu adalah peringatan (_red flag_) bahwa laba perusahaan didominasi oleh trik akuntansi (akrual), bukan uang kas riil yang masuk dari operasi bisnis.

kalau Stakeholder investor sham jangka panjang, solusi ini kurang tepat karena mayoritas kerugian investor saham jangka panjang di sebabkan oleh 
1. Fundamental perusahaan memburuk
2. Kualitas laba buruk
3. Prospek bisnis/industrinya memburuk
4. Manajemen dan tata kelola buru
5. Valuasi terlalu mahal
6. Salah penilaian resiko

### Status API

| Komponen                | Variabel                    | Status di Sectors API |
| ----------------------- | --------------------------- | --------------------- |
| **Sloan Accrual Ratio** | Net Income / Earnings       | Ada                   |
|                         | Operating Cash Flow (OCF)   | Ada                   |
|                         | Total Assets periode tt     | Ada                   |
|                         | Total Assets periode t−1t-1 |  Ada                  |

# Manipulasi Lapooran
## Beneish M Score (Manipulasi Laporan)
$$M = -4.84 + 0.920(DSRI) + 0.528(GMI) + 0.404(AQI) + 0.892(SGI) + 0.115(DEPI) - 0.172(SGAI) - 0.327(LVGI) + 4.679(TATA)$$

**Variabel Model**

- **DSRI (Days Sales in Receivables Index):** Mengukur apakah piutang tumbuh lebih cepat daripada pendapatan, yang dapat mengindikasikan manipulasi penjualan.
- **GMI (Gross Margin Index):** Menilai apakah margin kotor memburuk (nilai > 1 menunjukkan penurunan margin). 
- **AQI (Asset Quality Index):** Mengevaluasi proporsi aset tidak lancar (di luar aset tetap/PPE) terhadap total aset. Peningkatan nilai menunjukkan potensi kapitalisasi biaya yang seharusnya dibebankan langsung.    
- **SGI (Sales Growth Index):** Mengukur pertumbuhan penjualan. Pertumbuhan yang sangat tinggi dapat memicu tekanan untuk mempertahankan ekspektasi kinerja, sehingga meningkatkan risiko manipulasi.
- **DEPI (Depreciation Index):** Menunjukkan apakah tingkat penyusutan melambat, yang dapat menaikkan laba periode berjalan secara artifisial.
- **SGAI (Sales, General, and Administrative Expenses Index):** Melacak beban penjualan, umum, dan administrasi (SG&A) terhadap pendapatan. Penurunan yang tidak wajar dapat mengindikasikan penangguhan beban.
- **LVGI (Leverage Index):** Mengukur perubahan total utang terhadap total aset. Peningkatan leverage mendorong insentif untuk memanipulasi laporan keuangan agar tidak melanggar perjanjian utang (kovenan).
- **TATA (Total Accruals to Total Assets):** Menilai seberapa besar laba perusahaan didukung oleh arus kas nyata. Angka akrual yang tinggi menunjukkan risiko manipulasi yang lebih besar.

**Interpretasi Skor**
- **$M > -2.22$**: Probabilitas tinggi bahwa perusahaan melakukan manipulasi laporan keuangan.
- **$M < -2.22$**: Probabilitas rendah terjadinya manipulasi keuangan.

_(Catatan: Beberapa analis keuangan menggunakan ambang batas $-1.78$, tetapi angka $-2.22$ tetap menjadi standar utama yang paling banyak digunakan berdasarkan publikasi asli Messod Beneish pada tahun 1999)._

### Status API

| Komponen | Variabel yang dibutuhkan                    | Status di API Sectors                                                                          |
| -------- | ------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| **DSRI** | Accounts Receivable, Revenue                | **Account Receiveble belum ditemukan**, Revenue tersedia                                       |
| **GMI**  | Revenue, Gross Profit                       | **Ada**                                                                                        |
| **AQI**  | Current Assets, PPE, Total Assets           | **PPE belum ditemukan**, CA & TA tersedia                                                      |
| **SGI**  | Revenue                                     | **Ada**                                                                                        |
| **DEPI** | Depreciation, PPE                           | **Depreciation & PPE belum ditemukan**                                                         |
| **SGAI** | SG&A Expense, Revenue                       | **SG&A belum terkonfirmasi**; `operating_expense` tersedia tetapi belum tentu sama dengan SG&A |
| **LVGI** | Total Liabilities, Total Assets             | **Ada**                                                                                        |
| **TATA** | Net Income, OCF, Depreciation, Total Assets | **Depreciation belum ditemukan**; NI, OCF & TA tersedia                                        |

https://dinastirev.org/JEMSI/article/view/3814/2102 (dari perusahaan manufaktur)

## Dechow F-Score
Dechow F-Score merupakan metode pendeteksian fraud yang mengembangkan metode perhitungan Beneish M-Score dan dinilai lebih komprehensif dibandingkan Beneish M-Score karena cakupan pengujian data meliputi keseluruhan dari Accounting and Auditing Enforcement Releases (AAERs) yang diterbitkan oleh SEC pada 1982 hingga 2005 dibandingkan dengan Beneish M-Score yang hanya meliputi AAERs pada 1982 hingga 1992 (Aghghaleh et al., 2016). Apabila hasil f-score menunjukkan hasil lebih besar dari 1, maka terdapat indikasi fraud pada perusahaan dan jika hasil menunjukkan lebih kecil dari 1 maka menunjukkan bahwa perusahaan tidak terindikasi fraud (Ratmono et al., 2020).

$$\text{Value} = -7.893 + 0.790(\text{RSST}) + 2.518(\text{REC}) + 1.191(\text{INV}) + 1.979(\text{SOFTASSETS}) + 0.171(\text{CASHSALES}) - 0.932(\text{ROA}) + 1.029(\text{ISSUE})$$

Dechow F-Score diformulasikan sebagai berikut:

Variabel dalam Dechow F-Score dovetail sebagai berikut:


| Variabel   | Formula                                                                                                                                                                                                                                                                                                                                                                                                                            |
| ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| RSST       | ( WC + NCO + FIN)/Average Total Assets<br><br>WC = [Current Assets – Cash and Short-term Investments] – [Current Liabilities – Debt in Current Liabilities];<br><br>NCO = [Total Assets – Current Assets – Investments and Advances – [Total Liabilities – Current Liabilities – Long-term Debt];<br><br>Fin = [Short-term Investments + Long-term Investments] – [Long-term Debt + Debt in Current Liabilities + Prederred Stock] |
| REC        | Accounts Receivables/Average Total Assets                                                                                                                                                                                                                                                                                                                                                                                          |
| INV        | Inventory/Average Total Assets                                                                                                                                                                                                                                                                                                                                                                                                     |
| SOFTASSETS | [Total Assets – PPE – Cash and cash equivalents]/Total Assets                                                                                                                                                                                                                                                                                                                                                                      |
| CASHSALES  | Percentage change in cash sales [Sales – Accounts Receivables]                                                                                                                                                                                                                                                                                                                                                                     |
| ROA        | [Earnings t/Average total assets t] – [Earnings t-1/Average total assets t-1]                                                                                                                                                                                                                                                                                                                                                      |
| ISSUE      | An indicator variable coded 1 if the firm issued securities during year t                                                                                                                                                                                                                                                                                                                                                          |
### Status API
Model probabilitas manipulasi laporan keuangan Dechow sangat bergantung pada rincian spesifik akun (seperti Piutang, Persediaan, dan Aset Tetap) yang tidak tercantum secara eksplisit pada contoh respons `GET /v2/financials/quarterly/{symbol}/`.

| **Komponen Dechow F-Score**                         | **Status di API**  | **Keterangan / Parameter yang Digunakan**                                                                                                                                                           |
| --------------------------------------------------- | ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **$\Delta$ ROA** (Perubahan Return on Assets)       | Ada                | Dapat dihitung menggunakan `earnings` dibagi rata-rata `total_assets`.                                                                                                                              |
| **Actual Issuance** (Penerbitan Utang/Saham)        | Ada                | Dapat diproksikan melalui arus kas pendanaan (`financing_cash_flow` positif) atau dilacak dari rincian `right_issue` pada `GET /v2/company/corporate-actions/{symbol}/`.                            |
| **RSST Accruals**                                   | Sebagian           | Variabel dasar pembentuk seperti `total_assets`, `cash_only`, `total_liabilities`, dan `total_debt` tersedia. Namun, rincian investasi spesifik yang dibutuhkan untuk formula murni RSST tidak ada. |
| **$\Delta$ Receivables** (Perubahan Piutang)        | **Tidak Tersedia** | _Field_ spesifik untuk Piutang Usaha (_Accounts Receivable_) tidak tercantum pada _output_ API neraca kuartalan.                                                                                    |
| **$\Delta$ Inventory** (Perubahan Persediaan)       | **Tidak Tersedia** | _Field_ spesifik untuk Persediaan (_Inventory_) tidak ada pada daftar respons JSON.                                                                                                                 |
| **$\Delta$ Cash Sales** (Perubahan Penjualan Tunai) | **Tidak Tersedia** | Membutuhkan nilai Penjualan (`revenue`) yang dikurangi dengan selisih Piutang Usaha. Karena Piutang tidak ada, nilai Penjualan Tunai tidak bisa diisolasi.                                          |
| **Soft Assets**                                     | **Tidak Tersedia** | Membutuhkan variabel _Property, Plant, and Equipment_ (PP&E) yang tidak dijabarkan secara mandiri di respons neraca API ini.                                                                        |
Sumber:

- Aghghaleh, S. F., Mohamed, Z. M., & Rahmat, M. M. (2016). Detecting Financial Statement Frauds in Malaysia: Comparing the Abilities of Beneish and Dechow Models. _Asian Journal of Accounting and Governance_, _7_(November), 57–65. https://doi.org/10.17576/ajag-2016-07-05
- Ratmono, D., Darsono, D., & Cahyonowati, N. (2020). Financial Statement Fraud Detection With Beneish M-Score and Dechow F-Score Model: An Empirical Analysis of Fraud Pentagon Theory in Indonesia. _International Journal of Financial Research_, _11_(6), 154. https://doi.org/10.5430/ijfr.v11n6p154

Irisan variabel API dari **Sectors Financial API v2** yang benar-benar tersedia dan dapat digunakan secara bersamaan untuk mendukung kalkulasi **Dechow F-Score** dan **Beneish M-Score** (terutama dari endpoint laporan keuangan kuartalan `GET /v2/financials/quarterly/{symbol}/` dan data harian) mencakup komponen-komponen berikut:

|**Variabel / Parameter API**|**Digunakan untuk Beneish M-Score**|**Digunakan untuk Dechow F-Score**|**Keterangan di API**|
|---|---|---|---|
|**`revenue`** (Sales)|Ya (untuk SGI, DSRI, GMI, SGAI)|Ya (sebagai basis ukuran aktivitas/skala)|Tersedia secara langsung di endpoint kuartalan.|
|**`gross_profit`** & **`cost_of_revenue`**|Ya (untuk perhitungan GMI / Gross Margin Index)|Ya (analisis tren margin laba)|Tersedia secara langsung di endpoint kuartalan.|
|**`total_assets`**|Ya (untuk AQI, TATA, LVGI)|Ya (sebagai pembagi normalisasi akrual & ROA)|Tersedia secara langsung di endpoint kuartalan.|
|**`current_liabilities`** & **`total_debt`** / **`total_liabilities`**|Ya (untuk komponen Leverage / LVGI)|Ya (untuk metrik struktur modal / leverage)|Tersedia secara langsung di endpoint kuartalan.|
|**`operating_cash_flow`** & **`earnings`** (Net Income)|Ya (untuk komponen TATA / Total Accruals to Total Assets)|Ya (untuk pengukuran kualitas laba & akrual dasar)|Tersedia secara langsung di endpoint kuartalan.|

## Kesimpulan Irisan

Kedua model sama-sama bergantung penuh pada **data laporan laba rugi dasar** (`revenue`, `gross_profit`, `earnings`) dan **pos neraca makro** (`total_assets`, `total_liabilities`, `operating_cash_flow`) yang sudah disediakan oleh API Sectors.


Namun, irisan variabel ini **belum cukup** untuk mengeksekusi kedua formula secara utuh (_full-formula_). Baik Dechow F-Score maupun Beneish M-Score sama-sama tertahan oleh variabel detail spesifik seperti _Accounts Receivable_ (Piutang Usaha), _Inventory_ (Persediaan), dan _Net PP&E_ (Aset Tetap) yang tidak dirinci secara terpisah di dalam contoh respons JSON endpoint finansial standar API tersebut.

|**Variabel yang Hilang**|**Diperlukan oleh Beneish M-Score**|**Diperlukan oleh Dechow F-Score**|**Keterangan / Dampak pada Model**|
|---|---|---|---|
|**Accounts Receivable** (Piutang Usaha)|**Ya** (untuk DSRI - _Days Sales in Receivables Index_)|**Ya** (untuk komponen perubahan piutang / $\Delta$ Receivables)|Tanpa variabel ini, indeks lonjakan piutang fiktif pada Beneish dan penyesuaian modal kerja berbasis piutang pada Dechow tidak dapat dihitung.|
|**Inventory** (Persediaan)|**Tidak**|**Ya** (untuk komponen perubahan persediaan / $\Delta$ Inventory)|Menghambat kalkulasi perubahan aset lancar non-kas secara spesifik pada model Dechow.|
|**Net PP&E** (Property, Plant, and Equipment / Aset Tetap Bersih)|**Ya** (untuk DEPI - _Depreciation Index_)|**Ya** (untuk metrik _Soft Assets_ / rasio aset tetap terhadap total aset)|Tidak dapat menghitung indeks penurunan tingkat depresiasi (_Depreciation Index_) di Beneish serta rasio struktur aset di Dechow.|
|**SG&A Expense** (Biaya Penjualan, Umum, & Administrasi)|**Ya** (untuk SGAI - _SGA Expense Index_)|**Tidak**|Membuat indeks kenaikan beban operasional terhadap penjualan pada Beneish M-Score tidak bisa diproses.|
|**Securities / Current Investments** (Investasi Jangka Pendek non-kas)|**Ya** (untuk SGI - _Sales Growth Index_ / perhitungan aset lancar alternatif)|**Tidak**|Menyulitkan isolasi komponen aset lancar murni di luar kas pada beberapa varian turunan Beneish.|
