# 安装、维护与验证

## 依赖与位置

正常使用需要支持 Skill 的 Agent 宿主；账号/浏览器权限由用户环境提供。命令行检查需要 Python 3.10+，打包与 YAML 校验需要 PyYAML 6.x；Git 目标检查还需 Git。先复用已有环境，需要时运行 `python -m pip install -r requirements-dev.txt`。这一步会联网下载依赖；检查脚本本身不联网。

本仓库根目录就是 Skill，入口名 `git-rule-publish`。安装根目录使用宿主的 CODEX_HOME/skills，未设置时使用用户目录下 `.codex/skills`。已存在同名个人版本时不要覆盖；先完整备份，或保留公开版源码单独使用。此仓库不会自动修改已安装的个人版。

## 检查与打包

```text
python scripts/manage.py check
python scripts/public_check.py
python scripts/check_readme.py --root .
python -m unittest discover -s tests -v
python scripts/manage.py build --output <安装目录外的新ZIP路径>
python scripts/manage.py verify-zip --archive <ZIP路径>
```

`version.json` 明确列出包文件；不列入的个人配置、缓存或材料不会打包。ZIP 使用固定文件顺序和元数据，相同输入得到相同摘要；已有 ZIP 不覆盖。验包将归档与本地已校验源码比较，不能证明未知下载来源可信。

合法修改后先审查 diff、更新版本/CHANGELOG/文件清单，再运行 `python scripts/manage.py refresh-manifest`，随后重新测试。不要为消除报错直接接受不明修改。公开扫描只检测常见凭证形状和私人路径，不替代人工检查。

## 升级与回滚

下载后先在安装目录外核对 Release、摘要、结构和检查结果，再替换自己选定的安装副本。保留本地配置于独立备份，不写入公开包；未知本地改动先处理。回滚恢复自己的备份并开启新对话，旧对话不保证热更新。项目中的研究成果或其他代码不属于 Skill 安装目录，更新不应删除它们。

## 验证范围

自动测试验证包完整性、边界输入与辅助脚本；README 校验不验证所有文字事实或远程链接。行为场景需在隔离环境实际运行并记录结果，不能由单元测试数量推断模型成功率。真实平台访问、GitHub 登录和外部服务能力随用户环境而变。
