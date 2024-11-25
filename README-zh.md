# kytuning-client

#### 介绍
在OS基准性能优化过程中，常面临基准测试工具多样、数据对比繁琐，缺少高效的工具用于性能问题分析。kytuning 提供一个工具帮助完成繁琐重复性的工作释放人力，让工程师专注于性能问题的分析解决。

kytuning 初期计划支持基准测试工具如下：
- unixbench
- lmbench
- fio
- iozone
- specjvm2008
- stream
- speccpu2006
- speccpu2017

#### 软件架构

kytuning测试系统整体架构中主要三个角色：目标测试机，kytuning测试系统服务，web管理客户端。

kytuning-client 是作为目标测试机运行的软件, 其内部流程如下：

![图1](./imgs/kytuning-client流程图.png)
    


#### 安装教程

1.  安装依赖库：pip install -r  requirements.txt

#### 使用说明

1.  部署服务端，测试完成后可把测试结果上传至服务端。
2.  不部署服务端，也可以单独运行kytuning-client。
3.  下载kytuning-client。
4.  运行sh run.sh

#### 参与贡献

1.  Fork 本仓库
2.  提交代码
3.  新建 Pull Request


#### 特技

1.  使用 Readme\_XXX.md 来支持不同的语言，例如 Readme\_en.md, Readme\_zh.md
2.  Gitee 官方博客 [blog.gitee.com](https://blog.gitee.com)
3.  你可以 [https://gitee.com/explore](https://gitee.com/explore) 这个地址来了解 Gitee 上的优秀开源项目
4.  [GVP](https://gitee.com/gvp) 全称是 Gitee 最有价值开源项目，是综合评定出的优秀开源项目
5.  Gitee 官方提供的使用手册 [https://gitee.com/help](https://gitee.com/help)
6.  Gitee 封面人物是一档用来展示 Gitee 会员风采的栏目 [https://gitee.com/gitee-stars/](https://gitee.com/gitee-stars/)
