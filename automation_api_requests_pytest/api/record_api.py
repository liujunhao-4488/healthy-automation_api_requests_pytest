# api/record_api.py
# 【接口层】饮食记录：提交 / 列表 / 详情 / 删除。
#
# 为什么这四个放一个文件：它们是**一条链**，顺序写死才有意义：
#     submit 拿到 id → list 里能查到 → detail 能查到明细 → delete 后全部查不到
# 拆成四个文件的话，"这条链走到哪一步断了"要靠人脑拼。
#
# ⚠️ 两个实测出来、和文档/直觉不一样的地方，写在这里免得每次重新试：
#
#   ① **/record/list 的 page / pageSize 完全不生效**（缺陷 #17）。
#      传 pageSize=2 也返回全部 6 条，page=2 和 page=1 结果一模一样。
#      方法照常提供这两个参数，因为**用例需要用它来验证这个缺陷**；
#      但业务断言千万别写成"第 2 页应该有 2 条"——那是在替后端编造行为。
#
#   ② **detail 返回的是"明细数组"，不是"记录对象"**。
#      GET /record/detail/{id} 的 data 是 diet_record_detail 的行列表，
#      记录本身的字段（日期、餐次、总热量）要从 /record/list 里拿。
#      名字叫 detail 却只给明细，容易写成 data["recordDate"] 然后 KeyError。

from .base_api_client import BaseApiClient


class RecordApi(BaseApiClient):

    def submit(self, data, headers=None):
        """POST /record/submit —— 提交一条饮食记录，返回里带新记录的 id。

        data 的形状（API.md 7.1）：

            {"date": "2026-11-06",
             "mealType": "breakfast",          # breakfast/lunch/dinner/snack
             "notes": "早餐",
             "details": [{"foodName": "燕麦", "amount": 50, "unit": "g",
                          "calories": 194, "protein": 6.6, "carbs": 33.5, "fat": 3.1}]}

        ⚠️ details 里的 amount 会落到库里的 quantity 列，名字对不上是历史原因；
           断言时按响应的字段名（quantity）读，别按请求的字段名。
        """
        return self.post("/record/submit", json=data, headers=headers)

    def list_records(self, page=1, page_size=10, start_date=None, end_date=None, headers=None):
        """GET /record/list —— 饮食记录列表。

        返回 data 是**扁平数组**，不是 {list, total, page} 那种分页对象
        （对比 /article/list 就是标准分页对象）—— 两个接口风格不统一，
        写用例时别套用同一个解析函数。

        ⚠️ page / page_size 目前是**装饰性参数**，见文件头缺陷 #17。
           这里照样拼进查询串，是为了让"分页无效"这件事有地方可断言。
        """
        params = {"page": page, "pageSize": page_size}
        if start_date is not None:
            params["startDate"] = start_date
        if end_date is not None:
            params["endDate"] = end_date
        return self.get("/record/list", params=params, headers=headers)

    def detail(self, record_id, headers=None):
        """GET /record/detail/{recordId} —— 返回该记录的**明细数组**。

        别人的记录 / 不存在的记录，实测都是同一句 400「记录不存在或无权限查看」，
        不做区分（防枚举，和通知模块同一个设计思路）。
        """
        return self.get(f"/record/detail/{record_id}", headers=headers)

    def delete_record(self, record_id, headers=None):
        """DELETE /record/{recordId} —— 删除记录（软删，库里 is_deleted 置 1）。

        ⚠️ 方法名**不能叫 delete**：基类的 delete(path) 是"发一个 DELETE 请求"，
           重名会把底座那个覆盖掉，然后 self.delete(...) 无限递归 —— 报
           RecursionError，跟业务毫无关系，排查时很容易走错方向。
           同理，任何子类方法都别用 get/post/put/delete 这四个名字。

        ⚠️ 不是幂等：删第二次会返回 400「记录不存在或无权限删除」。
           别按"收藏接口幂等"的经验套过来。
        """
        return self.delete(f"/record/{record_id}", headers=headers)
