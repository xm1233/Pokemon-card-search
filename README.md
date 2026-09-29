# Pokemon-card-search

本机打开的搜索页。输入宝可梦的简体中文名，通过 [TCG API](https://tcgapi.dev/) 搜索宝可梦英文卡，展示卡图、套装信息与 TCGPlayer 参考价。页面说明为简体中文；卡名、套装名、招式描述为英文。属性名会显示成火、水、草、电等简体说法。

简体物种名来自本地字典。页面可切换 **TCG API**（含 TCGPlayer 参考价、仅宝可梦卡）或 **TCGdex**（英文国际版、不消耗 TCG API 每日额度）。

## 环境

- Python 3.10+
- 使用 **TCG API** 时：[TCG API](https://tcgapi.dev/dashboard) 的 API Key（环境变量 `TCGAPI_KEY`）及可访问 `api.tcgapi.dev` 的网络
- 使用 **TCGdex** 时：无需密钥，需可访问 TCGdex 服务

## 配置

复制示例并填入密钥（**不要提交 `.env`**）：

```powershell
copy .env.example .env
```

`.env` 示例：

```env
TCGAPI_KEY=tcg_live_你的密钥
```

也可直接设置系统环境变量 `TCGAPI_KEY`。官方 Python SDK 说明见 [Quick Start](https://tcgapi.dev/quickstart/)。

## 安装和启动

```powershell
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

浏览器打开 http://127.0.0.1:8000 。

在搜索框输入简体名前缀，例如「皮卡」。从候选里点选或按回车确定一只宝可梦后，才会去查卡。结果每页 24 张。点开一张卡可看大图、生命值、属性、招式（来自 API 的 `custom_attributes`）以及各印刷版本的参考价。

**注意：** 首次查询某只宝可梦时，后端会分页拉取 TCG API 搜索结果并缓存，会消耗较多每日请求额度。免费档为 [100 次/天](https://tcgapi.dev/)，请按需使用。

## 搜索怎么对上卡

字典在 `data/species.json`，每条是全国图鉴默认物种的简体名和英文名，例如「皮卡丘」对应 `Pikachu`。

1. 中文按前缀匹配。至少输入 1 个字。「皮卡」能命中「皮卡丘」，「丘」不能。候选最多 30 条。
2. 确定物种后，用英文名调用 TCG API 搜索（`type=Cards`），再在本地整词过滤。`Pikachu V` 会留下，`Mew` 不会留下 `Mewtwo`。
3. 读取 `custom_attributes.cardType`，只保留 `Pokemon`（不含训练家、场地、能量等）。Pro 套餐用 `bulk/cards` 批量拉取；免费档会自动改为逐张 `cards.get`，同一只宝可梦首次查询会多占若干次每日额度。
4. 弯引号 `’` 与直引号 `'` 在整词匹配时视为相同。

接口只接受字典里的英文名。首次查询某物种除搜索外还会按批拉取卡种信息，会多消耗若干次每日额度。

## 更新字典

```powershell
python scripts/build_species.py
```

运行时不会访问 PokeAPI。改完 `data/species.json` 后需重启服务。

## 已知限制

- 字典只有默认物种，没有区域形态别名（如「阿罗拉六尾」）。
- PokeAPI 英文名与 TCGPlayer 卡名不一致时，可能搜不到卡。
- 价格与 listing 来自 TCGPlayer，更新频率见 [TCG API 文档](https://tcgapi.dev/docs)。

## 测试

```powershell
python -m pytest tests -q
```

单元测试覆盖中文前缀与英文整词规则（不调用 TCG API）。
