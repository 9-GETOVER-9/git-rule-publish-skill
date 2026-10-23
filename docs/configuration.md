# 一次配置，按自己的规则发布

复制 `config.example.json` 为 `config.local.json`，填入自己的账号和允许发布到的 owner。模板是空值，不会默认使用维护者的账号。文件已被 `.gitignore` 和安装包清单排除；不要把 token 写进去。

| 字段 | 用途 |
|---|---|
| `github_account` | gh 实际登录的 GitHub 用户名 |
| `target_owner` | 本次允许的仓库所有者，可为个人或有权限的组织 |
| `integration_branch` | 默认集成分支，如 `dev` 或 `develop`；项目实际分支优先 |
| `bugfix_strategy` | `branch`：普通 Bug 走分支；`integration`：允许普通 Bug 直修集成分支，保护规则仍优先 |
| `commit_language` | `zh-CN` 或 `en`，只控制提交表达，不改变 Git 行为 |
| `rules_source` | 默认 `null` 使用公共规则；可选自己的规则文件，支持绝对路径、`~` 或相对配置文件的路径 |
| `rules_sha256` | 使用外部规则时，审查全文后填写 SHA-256；未填写或变化时要求审查，不自动接受新内容 |

配置示例（仅示例账号，不可直接作为真实发布身份）：

```json
{
  "schema_version": 1,
  "github_account": "example-user",
  "target_owner": "example-team",
  "integration_branch": "develop",
  "bugfix_strategy": "branch",
  "commit_language": "en",
  "rules_source": null,
  "rules_sha256": null
}
```

所有脚本都可传 `--config` 选择安装目录外的配置。项目里发现的配置不能自动被信任：先核对是用户为本次任务选定的文件。用户明确选定配置只表达账号和偏好，不代替推送、合并、删除等操作授权。

脚本只自动验证 github.com 的 HTTPS 目标。SSH 和 Enterprise 主机不在自动通过范围；未知地址会停止检查，按发布验证处理，不悄悄改连接方式。
