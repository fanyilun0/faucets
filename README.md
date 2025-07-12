# Faucet模板 - 通用水龙头请求工具

一个基于Python的通用faucet模板，支持配置化、代理、验证码自动处理，可快速复用于不同的区块链项目faucet。

## 特性

- ✅ **配置化设计** - 通过JSON配置文件快速适配不同faucet
- ✅ **代理支持** - 支持HTTP/SOCKS5代理，随机选择使用
- ✅ **验证码处理** - 集成2captcha服务，自动解决reCAPTCHA
- ✅ **重试机制** - 支持自动重试和间隔设置
- ✅ **日志记录** - 详细的日志记录，支持调试模式
- ✅ **响应检查** - 可配置的成功/失败检查机制

## 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt

# 复制环境变量模板
cp env.example .env
```

### 2. 配置环境变量

编辑 `.env` 文件：

```env
# 2captcha API Key (必需)
TWOCAPTCHA_API_KEY=your_2captcha_api_key_here

# 请求超时时间（秒）
REQUEST_TIMEOUT=30

# 验证码求解超时时间（秒）
CAPTCHA_TIMEOUT=120

# 是否启用详细日志
DEBUG_MODE=false
```

### 3. 配置faucet参数

编辑 `config.json` 文件：

```json
{
  "name": "Octra Faucet",
  "url": "https://faucet.octra.network/claim",
  "method": "POST",
  "headers": {
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
  },
  "address_key": "address",
  "recaptcha_key": "g-recaptcha-response",
  "recaptcha_site_key": "6LekoXkrAAAAAMlLCpc2KJqSeUHye6KMxOL5_SES",
  "additional_params": {
    "is_validator": false
  },
  "log_file": "faucet.log",
  "success_indicators": ["success", "claimed","tx-hash"],
  "error_indicators": ["error", "failed", "limit"],
  "retry_delay": 5,
  "max_retries": 3,
  "faucet_delay": 5
} 
```

### 4. 配置代理（可选）

编辑 `proxy.txt` 文件：

```txt
# 支持格式：
http://127.0.0.1:8080
socks5://127.0.0.1:1080
http://username:password@proxy.example.com:8080
```

### 5. 运行

```bash
python main.py
```

## 配置说明

### config.json 参数说明

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `name` | string | faucet名称 | "Octra Faucet" |
| `url` | string | 请求URL | "https://faucet.octra.network/claim" |
| `method` | string | 请求方法 | "POST" 或 "GET" |
| `headers` | object | 请求头 | 见示例配置 |
| `address_key` | string | 地址参数名 | "address" |
| `recaptcha_key` | string | 验证码参数名 | "g-recaptcha-response" |
| `recaptcha_site_key` | string | reCAPTCHA站点密钥 | "6LekoXkrAAAAAMlL..." |
| `additional_params` | object | 额外参数 | `{"is_validator": false}` |
| `success_indicators` | array | 成功指示符 | `["success", "claimed"]` |
| `error_indicators` | array | 失败指示符 | `["error", "failed", "limit"]` |
| `retry_delay` | number | 重试间隔（秒） | 5 |
| `max_retries` | number | 最大重试次数 | 3 |
| `facuet_delay` | number | faucet成功后的间隔（秒） | 5 |

### 代理配置

支持的代理格式：
- `http://host:port`
- `socks5://host:port`
- `http://username:password@host:port`
- `socks5://username:password@host:port`

## 使用示例

### 基本使用

```python
from main import FaucetTemplate

# 创建faucet实例
faucet = FaucetTemplate("config.json")

# 请求faucet
address = "your_wallet_address_here"
success, message = faucet.claim(address, use_proxy=True)

if success:
    print(f"✅ 成功: {message}")
else:
    print(f"❌ 失败: {message}")
```

### 批量请求

```python
addresses = [
    "address1",
    "address2", 
    "address3"
]

for address in addresses:
    success, message = faucet.claim(address, use_proxy=True)
    print(f"{address}: {'✅' if success else '❌'} {message}")
    
    # 请求间隔
    time.sleep(10)
```

## 日志

程序会生成详细的日志文件 `faucet.log`，包含：
- 请求详情
- 代理使用情况
- 验证码处理状态
- 成功/失败记录
- 错误详情

## 注意事项

1. **2captcha余额** - 确保2captcha账户有足够余额
2. **请求频率** - 遵守faucet的请求频率限制
3. **代理质量** - 使用高质量代理以提高成功率
4. **配置检查** - 确保配置参数正确无误

## 故障排除

### 常见问题

1. **验证码解决失败**
   - 检查2captcha API密钥是否正确
   - 确认账户余额充足
   - 验证站点密钥是否正确

2. **请求失败**
   - 检查网络连接
   - 验证URL和参数是否正确
   - 尝试不同的代理

3. **配置错误**
   - 检查JSON格式是否正确
   - 确认所有必需参数都已设置

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。 