# GitHub 同步说明

## 当前远端

- 仓库：`https://github.com/pythone1/yj_coder.git`
- 已上传分支：`online-resume-workspace`
- Pull Request 地址：`https://github.com/pythone1/yj_coder/pull/new/online-resume-workspace`

## 本机无法直接推送的原因

本机 DNS 将 `github.com` 解析到 `20.205.243.166`，但该 IP 的 443 端口 TCP 连接失败。

已验证：

- `github.com:443 -> 20.205.243.166`：失败
- `api.github.com:443`：成功
- `ssh.github.com:443`：成功，但本机没有配置 SSH 公钥，不能用 SSH 推送
- GitHub 其他前端 IP（如 `140.82.112.4`）可连通

## 可用推送命令

使用 Git 的临时解析配置，不修改系统 hosts：

```powershell
git -c http.version=HTTP/1.1 -c http.curloptResolve=github.com:443:140.82.112.4 push -u origin online-resume-workspace
```

如果该 IP 临时不可用，可替换为已测可通的：

```text
140.82.112.3
140.82.112.4
140.82.113.3
140.82.113.4
140.82.114.4
```

## 建议

远端 `main` 已经是分类作品仓库结构，当前分支是完整本地软件根目录。合并前建议在 GitHub 页面新建 PR 后检查差异；如果希望更清爽，可后续基于远端 `main` 新建一个目录，例如 `00-online-resume-editor/`，再把本软件整体放入该目录。
