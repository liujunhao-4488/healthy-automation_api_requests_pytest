import axios, { apiBaseUrl } from '../utils/axios';

/**
 * 把一个 SSE 事件块解析成 { event, data }。
 *
 * SSE 的文本格式长这样（事件之间用空行隔开）：
 *   event: delta
 *   data: {"text":"你"}
 *
 * 规则细节：`data:` 后面若紧跟一个空格，那个空格是分隔符、不算内容 —— 所以要剥掉。
 */
const parseEventBlock = (block) => {
  let event = 'message';
  const dataLines = [];

  block.split(/\r?\n/).forEach((line) => {
    if (line.startsWith('event:')) {
      event = line.slice(6).trim();
    } else if (line.startsWith('data:')) {
      dataLines.push(line.slice(5).replace(/^ /, ''));
    }
  });

  return { event, data: dataLines.join('\n') };
};

/**
 * 用 fetch + ReadableStream 消费 SSE。
 *
 * 为什么不用浏览器自带的 EventSource：
 *   ① 它只能发 GET，而助手这个接口是 POST（要带 body）；
 *   ② 它不能自定义请求头 —— 也就带不上 Authorization。
 * 为什么不用 axios：axios 拿到的是**整段读完**之后的响应，没有"边到边处理"的能力，
 *   流式就白做了。
 *
 * handlers 是一个"事件名 → 回调"的字典，例如 { start, delta, done, error }。
 * 返回 Promise：整条流读完才 resolve；中途出错（网络断、HTTP 非 2xx、回调里抛异常）则 reject。
 */
const streamSse = async (path, payload, handlers = {}) => {
  const token = localStorage.getItem('token');

  const response = await fetch(`${apiBaseUrl}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: JSON.stringify(payload || {})
  });

  if (!response.ok || !response.body) {
    let message = `请求失败（HTTP ${response.status}）`;
    try {
      const body = await response.json();
      if (body && body.message) {
        message = body.message;
      }
    } catch (ignored) {
      // 响应体不是 JSON（比如 401 的空体）—— 用默认文案
    }
    throw new Error(message);
  }

  const dispatch = (block) => {
    const { event, data } = parseEventBlock(block);
    if (!data) {
      return;
    }
    let parsed;
    try {
      parsed = JSON.parse(data);
    } catch (ignored) {
      return;
    }
    const handler = handlers[event];
    if (typeof handler === 'function') {
      handler(parsed);
    }
  };

  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';

  // 分帧要点：一次网络读取**可能只拿到半个事件**，所以没凑齐的尾巴要留在 buffer 里，
  // 等下一片凑上再解析。直接用"整块 JSON.parse"是做不到这一点的 ——
  // 这正是流式解析和"请求-响应"解析最大的不同。
  for (;;) {
    const { value, done } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });

    let match = buffer.match(/\r?\n\r?\n/);
    while (match) {
      dispatch(buffer.slice(0, match.index));
      buffer = buffer.slice(match.index + match[0].length);
      match = buffer.match(/\r?\n\r?\n/);
    }
  }

  // 收尾：最后一块可能没有以空行结尾
  if (buffer.trim()) {
    dispatch(buffer);
  }
};

export default {
  getConversations() {
    return axios.get('/assistant/conversations');
  },
  createConversation(payload) {
    return axios.post('/assistant/conversations', payload);
  },
  getMessages(conversationId) {
    return axios.get(`/assistant/conversations/${conversationId}/messages`);
  },
  chat(payload) {
    return axios.post('/assistant/chat', payload, { timeout: 60000 });
  },
  /**
   * 流式聊天（SSE）。
   *
   * 与非流式 chat 的区别只在"回答怎么回来"：这里一段段推给 handlers，
   * 而不是等整段生成完再一次性返回。落库、会话、消息结构都和 chat 一模一样。
   */
  chatStream(payload, handlers) {
    return streamSse('/assistant/chat/stream', payload, handlers);
  },
  deleteConversation(conversationId) {
    return axios.delete(`/assistant/conversations/${conversationId}`);
  }
};
