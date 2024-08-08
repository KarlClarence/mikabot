# AI Mika

GPT4的AI圣园未花角色bot

### 安装
运行需要python3环境
```bash
# 拉取仓库
$ git clone https://github.com/k96e/mika-ai

# 安装依赖
$ cd mika-ai
$ pip install -r requirements.txt
```

### 配置
编辑`bot.conf`，一般只需要填上`api_key`就行
```
api_key:        OpenAI api 密钥，必填
api_url:        OpenAI api base_url，如果需要修改可以取消注释
model:          对话使用的模型
listen,port:    WebUI监听的地址和端口
prompt_file:    提示词文件名
```
模型推荐使用不带turbo的原版`gpt-4`模型，效果更好，别问为啥我也不知道\
如需使用DeepSeek模型，取消注释`api_url`项并修改如下内容：
```
api_url = https://api.deepseek.com
model = deepseek-chat
```
然后在`api_key`处填入官网获取的api密钥
### 运行
```bash
$ python bot.py
```
默认情况下请使用浏览器打开 <http://127.0.0.1:8888> \
对话中可输入`cls`清空对话历史，`tokens`查询该轮对话tokens用量 \
使用反斜线`\`可以实现换行效果

### 叠甲
- 自用项目能跑就行，代码很烂
- 未花的设定基于个人理解肯定有失偏颇，而且我不建议你去读prompt文件
- 没有对提示词攻击做任何防范，钓鱼铁上钩
- 本地部署版暂时没做联网搜索和事实核查能力，涉及游戏设定和具体剧情的内容是肯定会瞎编的
- 不可以瑟瑟

注：MomoTalk页面样式参考萌娘百科的[Template:Momotalk](https://zh.moegirl.org.cn/Template:%E8%94%9A%E8%93%9D%E6%A1%A3%E6%A1%88Momotalk)，遵循 CC BY-NC-SA 3.0 CN 许可协议