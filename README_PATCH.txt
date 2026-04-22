替换这些文件到你的 design-agents 仓库即可。

本次修改目标：
1. Engine 的 provider / model / api_key / base_url 默认从 .env 读取；
2. Engine 实例化时显式传入的参数优先；
3. tests 下 3 个测试文件统一为同一模板，直接改顶部 CONFIG 即可；
4. 删除交互式 getpass / argparse 嵌套；
5. 修复 chat 历史重复注入问题；
6. 用 Toolbox.clone() 替代 Engine 内部 if/else 克隆逻辑。
