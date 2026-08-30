# `data/raw/` 输入清单（2026-08-30 实测编制）

本目录被 `.gitignore` 排除（约 1.6 GB）。下面是**代码实际读取**的每一个文件，
以及它到底能不能由 `src/data_prep/00_download_all_data.py` 自动获得。

> ⚠️ 编制方式：把 `src/data_prep/*.py` 与 `src/model/*.py` 里所有 `RAW / "..."` 引用
> 全部抓出来去重，再逐个对照下载脚本的实现。不是照抄文档。

## 一、脚本能自动下载的（4 项）

| 文件 | 来源 | 脚本位置 |
|---|---|---|
| `hydro_network/ohn_watercourse.geojson` | LIO Open Data MapServer 图层 26 | `LIO_LAYERS`，`download_lio_layer()` |
| `hydro_network/tile_drainage.geojson` | 同上，图层 11 | 同上 |
| `hydro_network/constructed_drain.geojson` | 同上，图层 7 | 同上 |
| `omafra_field_crop_budgets_2025.pdf` | ontario.ca 直链 | `00:151` |

## 二、脚本**下不了**、必须手动准备的（5 项）

| 文件 | 谁在用 | 怎么拿 | 脚本尾部有没有提醒 |
|---|---|---|---|
| `soil_survey/soil_survey_complex_ft.tbl` | `02_build_p_risk_map.py:49` | 安大略土壤调查（OMAFRA/AAFC） | ⛔ **没提** |
| `soil_survey/soilomaf.shp`（含 .dbf/.shx/.prj） | `02_build_p_risk_map.py:59` | 同上 | ⛔ **没提** |
| `land_use/aci_2024_on/aci_2024_on_v2.tif` | `03_build_field_agents.py:88` | AAFC Annual Crop Inventory 2024（安大略） | ⛔ **没提** |
| `dem/` | `01_*`（地形派生） | 脚本提示：GeoHub 搜 "Provincial DEM"，或 USGS SRTM | ✅ 提了 |
| `farm_parcels/` | 田块构建 | 脚本提示：`librarygeo@library.uwaterloo.ca` | ✅ 提了 |

## 三、既下不了、也没被提醒的一项

`watershed_boundaries/owb_tertiary.geojson` —— `download_watershed_boundaries()`
只探测端点、**从不写文件**。脚本尾部提到 "UTRCA subwatershed boundaries" 指的是
`thamesriver-camaps.hub.arcgis.com`，与这个 OWB tertiary 图层不是同一份东西。

## 四、⚠️ 一处已修的自我矛盾

`.gitignore` 原第 1 行写的是

```
# Raw downloaded spatial data (1.7 GB; reproducible via src/data_prep/00_download_all_data.py)
```

而 `00_download_all_data.py:188-191` 自己打印

```
Manual downloads still needed:
  - DEM / Parcel data / UTRCA subwatershed boundaries
```

**仓库自述与脚本自述直接打架**，而且两边都不完整：脚本列了 3 项，实际缺 6 项。
`.gitignore` 那行已改为指向本文件。

## 五、这意味着什么

`RUN_GUIDE.md` 的 "Full reproduction from scratch" 路径，克隆者跑到 `02` 就会
`FileNotFoundError`。**这不是「跑一遍就好」的问题** —— 缺的是需要走机构渠道
（UW 图书馆地理空间部）或需要具体下载 URL 的数据。

对本仓 owner 不可见：这些文件在本机工作副本里全都在，只是被 gitignore 挡在分发包外。
