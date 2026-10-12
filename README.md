# Pokemon-card-search

本机打开的搜索页。输入宝可梦的简体中文名，通过 [TCGdex](https://tcgdex.dev/) 搜索英文国际版卡，展示卡图、套装、生命值、属性和招式。页面说明为简体中文；卡名、套装名、招式描述为英文。属性名会显示成火、水、草、电等简体说法。

简体物种名来自本地字典。不需要 API 密钥。

## 环境

- Python 3.10+
- Node.js（启动 Vue 页面时用）
- 可访问 TCGdex 服务

## 安装和启动

页面只由 Vue 开发服务提供。后端只提供查询接口，不托管页面。

### 安装

```powershell
python -m pip install -r requirements.txt
cd frontend
npm install
```

### 启动后端

在项目根目录：

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 启动前端

另开终端：

```powershell
cd frontend
npm run dev
```

浏览器打开 http://127.0.0.1:5173 。页面上的 `/api` 请求会转到 8000，所以后端要先在跑。只开后端时，8000 上没有页面。

在搜索框输入简体名前缀，例如「皮卡」。从候选里点选或按回车确定一只宝可梦后，才会去查卡。结果每页 24 张。点开一张卡可看大图、生命值、属性和招式。

**注意：** 首次查询某只宝可梦时，后端会向 TCGdex 分页拉取搜索结果并缓存在内存里。

## 搜索怎么对上卡

字典在 `data/species.json`，每条是全国图鉴默认物种的简体名和英文名，例如「皮卡丘」对应 `Pikachu`。

1. 中文按前缀匹配。至少输入 1 个字。「皮卡」能命中「皮卡丘」，「丘」不能。候选最多 30 条。
2. 确定物种后，用英文名向 TCGdex 查询，再在本地整词过滤。`Pikachu V` 会留下，`Mew` 不会留下 `Mewtwo`。
3. 弯引号 `’` 与直引号 `'` 在整词匹配时视为相同。

接口只接受字典里的英文名。

## 更新字典

```powershell
python scripts/build_species.py
```

运行时不会访问 PokeAPI。改完 `data/species.json` 后需重启服务。

## 已知限制

- 字典只有默认物种，没有区域形态别名（如「阿罗拉六尾」）。
- PokeAPI 英文名与 TCGdex 卡名不一致时，可能搜不到卡。
- 不提供 TCGPlayer 价格。

## 测试

```powershell
python -m pytest tests -q
```

单元测试覆盖中文前缀与英文整词规则（不调用 TCGdex）。
