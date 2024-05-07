#!/usr/bin/env python
# -*- coding:utf-8 -*-

# Author : zhibo.wang
# E-mail : gm.zhibo.wang@gmail.com
# Date   :
# Desc   :


try:
    from common.log import logger
    from plugins import *
    from bridge.context import ContextType
    from bridge.reply import Reply, ReplyType
    from channel.chat_message import ChatMessage
    import os
    # import re
    import json
    import time
    import plugins
    import datetime
    import requests
    import uuid
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except Exception as e:
    logger.error(f"[botcloud] import error: {e}")


@plugins.register(
    name="botmaxkb",                      # 插件的名称
    desire_priority=100,                  # 插件的优先级 数据越大优先级越高
    hidden=False,                         # 插件是否隐藏
    desc="maxkb AI助手",                  # 插件的描述
    version="0.0.1",                      # 插件的版本号
    author="gm.zhibo.wang@gmail.com",     # 插件的作者
)
class Botmaxkb(Plugin):


    def __init__(self):
        super().__init__()
        tag = "botcloud 初始化"
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        try:
            self.conf = super().load_config()
            self.kb_api_host = self.conf.get("kb_api_host", "http://127.0.0.1:8080")
            self.kb_api_key = self.conf.get("kb_api_key", "application-6b539b9bea1055ef9b61dffa351b3c23")
            self.chat_id = None

            logger.info("[botcloud] inited")
        except Exception as e:
            log_msg = f"{tag}: error: {e}"
            logger.error(log_msg)

    def on_handle_context(self, e_context: EventContext, retry_count: int = 0):
        """
        TEXT = 1           # 文本消息
        """
        if e_context["context"].type not in [
            ContextType.TEXT,
        ]:
            return
        e_msg: ChatMessage = e_context["context"]["msg"]
        context = e_context["context"]
        content = context.content.strip()
        user_id = e_msg.from_user_id
        logger.info(f"[Botcloud] on_handle_context. user_id: {user_id}, content: {content}")
        if e_context["context"].type == ContextType.TEXT:
            tag = "AI助手"
            msg = self.fun_cloud_kb(content, tag)
            content = msg
            reply = self.create_reply(ReplyType.TEXT, tag, content)
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS

    def create_reply(self, reply_type, tag, content):
        reply = Reply()
        reply.type = reply_type
        content = f"{tag}\n{content}"
        reply.content = content
        return reply

    def get_help_text(self, verbose=False, **kwargs):
        help_text = "发送关键词执行对应操作\n"
        if not verbose:
            return help_text
        help_text += "输入 '内容'， 进行本地知识库解答\n"
        return help_text


    def get_kb_chat_id(self):
        # 应用id 获取会话id
        tag = "获取会话id"
        application_id = "a738eda0-0b4f-11ef-bbef-0242ac120002"
        chat_id = None
        try:
            url = f"{self.kb_api_host}/api/application/{application_id}/chat/open"
            headers = {
                "Accept": "application/json",
                "Authorization": self.kb_api_key
            }
            response = requests.request("GET", url, headers=headers, timeout=30)
            r_code = response.status_code
            if r_code == 200:
                res_json = response.json()
                json_code = res_json.get("code")
                if json_code == 200:
                    chat_id = res_json.get("data")
                else:
                    log_msg = f"{tag}: response json code:{json_code}"
                    logger.info(log_msg)
            else:
                log_msg = f"{tag}: response status_code:{r_code}"
                logger.info(log_msg)
        except Exception as e:
            logger.error(f"{tag}: 服务器内部错误 {e}")
        return chat_id

    def fun_cloud_kb(self, gpt_text, tag):
        # kb 本地知识库
        msg = f"{tag}: 服务器睡着了,请稍后再试"
        try:
            payload = json.dumps({
                "message": "数据问题",
                "re_chat": False,
                "stream": False
            })
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": self.kb_api_key
            }
            for i in range(3):
                if self.chat_id is None:
                    chat_id = self.get_kb_chat_id()
                    if chat_id:
                        self.chat_id = chat_id
                url = f"{self.kb_api_host}/api/application/chat_message/{self.chat_id}"
                response = requests.request("POST", url, headers=headers, data=payload, timeout=60)
                r_code = response.status_code
                if r_code == 200:
                    res_json = response.json()
                    json_code = res_json.get("code")
                    if json_code == 200:
                        msg = res_json.get("data").get("content")
                        break
                    else:
                        log_msg = f"{tag}: response json code:{json_code}"
                        logger.info(log_msg)
                        # 失效 重拿

                else:
                    log_msg = f"{tag}: response status_code:{r_code}"
                    logger.info(log_msg)
                    # 失效 重拿
        except Exception as e:
            logger.error(f"{tag}: 服务器内部错误 {e}")
        return msg



