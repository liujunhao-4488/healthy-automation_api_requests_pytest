/**
 * AI 助手 · 前端输入预检（体验层，**不是安全边界**）
 *
 * ⚠️ 这段代码跑在客户端，可以被直接绕过（控制台构造请求、直调 /assistant/chat、改包）。
 *    所以它只负责**体验**：明显的垃圾输入本地就挡掉，省一次网络往返、反馈更快。
 *    真正的安全闸门在**后端** RecipeServiceImpl.detectBlockedType() —— 那里才不可绕过。
 *
 * ══ 职责边界（2026-10-13 收紧）══════════════════════════════════
 * 这里**只做两类**：超长、明摆着的脏话。
 *
 * 高危医疗（求药量 / 自行停药 / 自残）与无关领域（写代码 / 订机票 / 问天气…）
 * **整段交给后端**，前端不再判。原因不是"前端做不到"，而是"两份规则一定会漂移"：
 * 这两类要靠上下文判（后端有「越界词 + 饮食词同现则放行」的白名单），
 * 前端抄一份就会各自演化 —— 之前就漂移过：「今天天气冷了，适合喝什么汤」
 * 「早餐吃几片全麦面包合适」在前端被误拦、后端已放行。
 *
 * 命中规则时返回 { type, reply }（type: 'abuse' | 'too_long'），未命中返回 null。
 */

// 脏话 / 辱骂：单字「草」「操」误伤率高（草莓 / 甘草 / 体操），
// 只匹配明确的辱骂组合与拼音缩写。
// ⚠️ 这份词表**以后端 BLOCK_ABUSE_PATTERNS 为准**，两边必须一致，否则又会漂移。
//    末尾的 (?!) 负向断言全是实测抓出来的误伤：
//      · 我草(?![\u4e00-\u9fa5]) —— 否则「我草莓过敏」被判辱骂
//      · 我操(?![\u4e00-\u9fa5]) —— 同理
//      · 妈的(?![\u4e00-\u9fa5]) —— 否则「我妈妈的饮食建议」被判辱骂
const ABUSE_PATTERNS = [
  /cnm|nmsl|tmd|tnnd|woc|wc(?![a-z])|sb(?![a-z])|fuck|shit/i,
  /草泥马|艹你|艹尼玛|操你|操他|他妈的|你妈的|它妈的|妈的(?![\u4e00-\u9fa5])|妈逼|傻逼|煞笔|沙雕|狗东西|去死|卧槽|我操(?![\u4e00-\u9fa5])|我艹|我草(?![\u4e00-\u9fa5])/,
]

const REPLY_ABUSE =
  '请文明交流哦～我会尽力帮你解答饮食与健康相关的问题，比如食材替代、三餐搭配、热量营养估算等。'
const REPLY_TOO_LONG = '输入内容过长，请精简到 1000 字以内再提问。'

const MAX_INPUT_LENGTH = 1000

export const checkAssistantInput = (text) => {
  const input = text == null ? '' : String(text).trim()
  if (!input) {
    return null
  }

  // 超长（同时防超长刷接口）——纯长度判断，零误伤风险，留在前端最划算。
  if (input.length > MAX_INPUT_LENGTH) {
    return { type: 'too_long', reply: REPLY_TOO_LONG }
  }

  if (ABUSE_PATTERNS.some((pattern) => pattern.test(input))) {
    return { type: 'abuse', reply: REPLY_ABUSE }
  }

  // 其余一律放行 —— 交给后端判定（它才是不可绕过的那道闸门）。
  return null
}
