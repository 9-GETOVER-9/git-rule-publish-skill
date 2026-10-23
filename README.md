<div align="center">

# 星火燎原 · GitHub 发布与 README Skill

**把成果交付到正确仓库，把项目价值写进清晰、美观、可验证的 README。**

`账号可配置` · `真实推送目标检查` · `README 写作` · `发布可续接`

[![Stars](https://img.shields.io/github/stars/9-GETOVER-9/git-rule-publish-skill?style=for-the-badge&color=d6a85c&label=Stars)](https://github.com/9-GETOVER-9/git-rule-publish-skill/stargazers)
[![Version](https://img.shields.io/badge/version-v1.0.0-607d8b?style=for-the-badge)](https://github.com/9-GETOVER-9/git-rule-publish-skill/releases)
[![License](https://img.shields.io/badge/license-MIT-6b8f71?style=for-the-badge)](LICENSE)
[![Checks](https://img.shields.io/github/actions/workflow/status/9-GETOVER-9/git-rule-publish-skill/check.yml?branch=main&style=for-the-badge&label=Checks)](https://github.com/9-GETOVER-9/git-rule-publish-skill/actions/workflows/check.yml)

[快速安装](#install) · [使用示例](#usage) · [配置](#configuration) · [维护与测试](docs/maintenance.md)

</div>

---

> 适合使用 Agent 完成开发、希望按自己的规则上传 GitHub 的人。从账号与目标检查到 README 和版本交付，把容易遗漏的步骤写成可执行、可验证的工作流。

## 能做什么

| 能力 | 你会得到什么 |
|:---|:---|
| 配置自己的账号 | 个人/组织 owner 分开配置，不绑定维护者身份 |
| 推送目标核验 | 核对全部 push URL、具体仓库和 Git URL 重写 |
| 分支与提交习惯 | 普通 Bug 是否直修集成分支、提交语言可配置 |
| README 编写 | 居中首屏、真实徽章、最短安装路径、示例和折叠详情 |
| 发布与恢复 | 区分上传、PR、合并、Release；同版本内容冲突不盲目覆盖 |

<a id="install"></a>
## 快速安装

需要支持 `SKILL.md` 的宿主。以下命令安装到 Codex 默认位置；已存在同名个人 Skill 时不要覆盖，请保留原目录。克隆安装无需 Python；运行校验脚本需要 Python 3.10+，维护环境依赖见说明。

<details open>
<summary><b>macOS / Linux</b></summary>

```bash
skill_root="${CODEX_HOME:-$HOME/.codex}/skills"
mkdir -p "$skill_root"
git clone https://github.com/9-GETOVER-9/git-rule-publish-skill.git "$skill_root/git-rule-publish"
```

</details>

<details>
<summary><b>Windows PowerShell</b></summary>

```powershell
$skillRoot = if ($env:CODEX_HOME) { Join-Path $env:CODEX_HOME 'skills' } else { Join-Path $env:USERPROFILE '.codex/skills' }
New-Item -ItemType Directory -Force $skillRoot | Out-Null
git clone https://github.com/9-GETOVER-9/git-rule-publish-skill.git (Join-Path $skillRoot 'git-rule-publish')
```

</details>

也可从 [Releases](https://github.com/9-GETOVER-9/git-rule-publish-skill/releases) 下载 ZIP，解压后将顶层 `git-rule-publish` 文件夹放到自己的 Skill 目录。入口应为 `git-rule-publish/SKILL.md`，避免套多一层。开启新对话加载。

<a id="configuration"></a>
## 按你的习惯配置

上传前复制 `config.example.json` 为 `config.local.json`，填写自己的 `github_account` 和 `target_owner`；其他字段按 [配置说明](docs/configuration.md) 调整。空配置会停止发布，不会使用项目维护者账号。只制作 README 不需要 GitHub 登录。

本地配置已被 Git 和打包清单排除，别把 token 放进配置。仓库链接中的账号只是项目地址，不是运行身份。

<a id="usage"></a>
## 使用示例

```text
用 $git-rule-publish 整理这个项目的 README。
参考居中标题、徽章、快速安装和使用示例的布局，内容以源码和测试为准。
这次只改文档，不上传。
```

配置好账号后也可以说：

```text
按我的 config.local.json 上传本次成果到指定仓库，公开。
先完成检查，再推送；不要混入其他任务的改动。
```

## 工作流

```text
读取可信配置 → 核对任务与目标 → 完善 README → 测试与暂存 → 明确范围上传 / 发布
```

## 能力边界

自动目的地检查支持 github.com HTTPS；SSH 需要额外核验，检查通过也不等于已经验证身份、权限或 CI。Skill 不替用户购买权限，也不把“上传”解释为删除、强推或持续后台操作。

## 文档与维护

- [Skill 入口](SKILL.md)：实际执行指令。
- [配置](docs/configuration.md)：适配自己的环境和偏好。
- [维护与测试](docs/maintenance.md)：本地检查、打包、升级和回滚。
- [贡献与反馈](CONTRIBUTING.md) · [安全反馈](SECURITY.md) · [变更记录](CHANGELOG.md)。
- [来源与公开范围](NOTICE.md) · [MIT License](LICENSE)。

自动检查覆盖辅助脚本和交付边界；不能用通过的测试数量推断模型任务成功率。GitHub Actions 展示当前提交的真实检查状态。

想把这种排版用于其他项目，参阅 [README 编写流程](references/readme-design.md)、[可复用模板](assets/readme-template.md) 和 [行为验证范围](docs/behavior-checks.md)。
