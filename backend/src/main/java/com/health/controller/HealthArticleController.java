package com.health.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.UpdateWrapper;
import com.health.entity.ArticleComment;
import com.health.entity.HealthArticle;
import com.health.entity.User;
import com.health.entity.UserArticleCollect;
import com.health.entity.UserArticleLike;
import com.health.entity.UserReadRecord;
import com.health.mapper.ArticleCommentMapper;
import com.health.mapper.UserArticleCollectMapper;
import com.health.mapper.UserArticleLikeMapper;
import com.health.service.HealthArticleService;
import com.health.service.UserService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.security.Principal;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.stream.Collectors;

@Slf4j
@RestController
@RequestMapping("/article")
public class HealthArticleController {

    @Autowired
    private HealthArticleService healthArticleService;

    @Autowired
    private UserService userService;

    @Autowired
    private UserArticleCollectMapper userArticleCollectMapper;

    @Autowired
    private UserArticleLikeMapper userArticleLikeMapper;

    @Autowired
    private ArticleCommentMapper articleCommentMapper;

    @GetMapping("/list")
    public ResponseEntity<?> getHealthArticleList(
        @RequestParam(required = false) String category,
        @RequestParam(required = false) String tag,
        @RequestParam(required = false) String keyword,
        @RequestParam(required = false, defaultValue = "recommend") String sort,
        @RequestParam(required = false, defaultValue = "1") Integer page,
        @RequestParam(required = false, defaultValue = "10") Integer pageSize,
        Principal principal
    ) {
        try {
            Long userId = resolveUserId(principal);
            List<HealthArticle> filteredArticles = queryArticles(category, tag, keyword, sort);
            List<HealthArticle> pagedArticles = paginate(filteredArticles, page, pageSize);

            Map<String, Object> data = new HashMap<>();
            data.put("list", pagedArticles.stream().map(article -> toArticleView(article, userId)).collect(Collectors.toList()));
            data.put("total", filteredArticles.size());
            data.put("page", page);
            data.put("pageSize", pageSize);
            data.put("tags", buildTagList());
            return successResponse("获取健康文章成功", data);
        } catch (Exception e) {
            log.error("获取健康文章失败: {}", e.getMessage(), e);
            return badRequestResponse(e.getMessage());
        }
    }

    @GetMapping("/tags")
    public ResponseEntity<?> getArticleTags() {
        try {
            return successResponse("获取文章标签成功", buildTagList());
        } catch (Exception e) {
            log.error("获取文章标签失败: {}", e.getMessage(), e);
            return badRequestResponse(e.getMessage());
        }
    }

    @GetMapping("/detail/{articleId}")
    public ResponseEntity<?> getHealthArticleDetail(@PathVariable Long articleId, Principal principal) {
        try {
            Long userId = resolveUserId(principal);
            HealthArticle article = healthArticleService.getHealthArticleById(articleId, userId);
            if (article == null) {
                return badRequestResponse("文章不存在");
            }
            return successResponse("获取文章详情成功", toArticleView(article, userId));
        } catch (Exception e) {
            log.error("获取文章详情失败: {}", e.getMessage(), e);
            return badRequestResponse(e.getMessage());
        }
    }

    @GetMapping("/recommend")
    public ResponseEntity<?> getRecommendedArticles(
        Principal principal,
        @RequestParam(required = false, defaultValue = "1") Integer page,
        @RequestParam(required = false, defaultValue = "10") Integer pageSize,
        @RequestParam(required = false) Long excludeId
    ) {
        try {
            Long userId = resolveUserId(principal);
            List<HealthArticle> recommendedArticles = healthArticleService.getRecommendedArticles(userId, 0);
            if (excludeId != null) {
                recommendedArticles = recommendedArticles.stream()
                    .filter(article -> !excludeId.equals(article.getId()))
                    .collect(Collectors.toList());
            }
            List<HealthArticle> pagedArticles = paginate(recommendedArticles, page, pageSize);

            Map<String, Object> data = new HashMap<>();
            data.put("list", pagedArticles.stream().map(article -> toArticleView(article, userId)).collect(Collectors.toList()));
            data.put("total", recommendedArticles.size());
            data.put("page", page);
            data.put("pageSize", pageSize);
            data.put("tags", buildTagList());
            return successResponse("获取推荐文章成功", data);
        } catch (Exception e) {
            log.error("获取推荐文章失败: {}", e.getMessage(), e);
            return badRequestResponse(e.getMessage());
        }
    }

    @GetMapping("/read/history")
    public ResponseEntity<?> getReadHistory(
        Principal principal,
        @RequestParam(required = false, defaultValue = "6") Integer limit
    ) {
        if (principal == null) {
            return unauthorizedResponse();
        }

        try {
            Long userId = Long.parseLong(principal.getName());
            List<Map<String, Object>> history = healthArticleService.getUserReadHistory(userId, Math.max(1, limit));
            List<Map<String, Object>> data = history.stream()
                .map(item -> {
                    HealthArticle article = (HealthArticle) item.get("article");
                    Map<String, Object> view = toArticleView(article, userId);
                    view.put("readTime", item.get("readTime"));
                    view.put("readDuration", item.get("readDuration"));
                    view.put("scrollPercent", item.get("scrollPercent"));
                    view.put("finished", item.get("finished"));
                    return view;
                })
                .collect(Collectors.toList());
            return successResponse("获取阅读历史成功", data);
        } catch (Exception e) {
            log.error("获取阅读历史失败: {}", e.getMessage(), e);
            return badRequestResponse(e.getMessage());
        }
    }

    @PostMapping("/read/{articleId}")
    public ResponseEntity<?> recordArticleRead(
        @PathVariable Long articleId,
        @RequestBody(required = false) Map<String, Object> payload,
        Principal principal
    ) {
        if (principal == null) {
            return unauthorizedResponse();
        }

        try {
            Long userId = Long.parseLong(principal.getName());
            Integer readDuration = parseIntegerValue(payload == null ? null : payload.get("readDuration"));
            Integer scrollPercent = parseIntegerValue(payload == null ? null : payload.get("scrollPercent"));
            UserReadRecord readRecord = healthArticleService.recordArticleRead(userId, articleId, readDuration, scrollPercent);
            return successResponse("记录阅读成功", readRecord);
        } catch (Exception e) {
            log.error("记录阅读失败: {}", e.getMessage(), e);
            return badRequestResponse(e.getMessage());
        }
    }

    @GetMapping("/search")
    public ResponseEntity<?> searchHealthArticles(
        @RequestParam String keyword,
        @RequestParam(required = false, defaultValue = "1") Integer page,
        @RequestParam(required = false, defaultValue = "10") Integer pageSize,
        Principal principal
    ) {
        return getHealthArticleList(null, null, keyword, "recommend", page, pageSize, principal);
    }

    @PostMapping("/like/{articleId}")
    public ResponseEntity<?> likeArticle(@PathVariable Long articleId, Principal principal) {
        if (principal == null) {
            return unauthorizedResponse();
        }

        try {
            Long userId = Long.parseLong(principal.getName());
            QueryWrapper<UserArticleLike> wrapper = new QueryWrapper<>();
            wrapper.eq("user_id", userId).eq("article_id", articleId);

            if (userArticleLikeMapper.selectOne(wrapper) == null) {
                UserArticleLike like = new UserArticleLike();
                like.setUserId(userId);
                like.setArticleId(articleId);
                like.setCreateTime(LocalDateTime.now());
                userArticleLikeMapper.insert(like);
            }
            healthArticleService.syncArticleStats(articleId);

            Map<String, Object> data = new HashMap<>();
            data.put("liked", true);
            data.put("likeCount", getArticleLikeCount(articleId));
            return successResponse("点赞成功", data);
        } catch (Exception e) {
            log.error("点赞文章失败: {}", e.getMessage(), e);
            return badRequestResponse(e.getMessage());
        }
    }

    @DeleteMapping("/like/{articleId}")
    public ResponseEntity<?> cancelLikeArticle(@PathVariable Long articleId, Principal principal) {
        if (principal == null) {
            return unauthorizedResponse();
        }

        try {
            Long userId = Long.parseLong(principal.getName());
            QueryWrapper<UserArticleLike> wrapper = new QueryWrapper<>();
            wrapper.eq("user_id", userId).eq("article_id", articleId);
            userArticleLikeMapper.delete(wrapper);
            healthArticleService.syncArticleStats(articleId);

            Map<String, Object> data = new HashMap<>();
            data.put("liked", false);
            data.put("likeCount", getArticleLikeCount(articleId));
            return successResponse("已取消点赞", data);
        } catch (Exception e) {
            log.error("取消点赞失败: {}", e.getMessage(), e);
            return badRequestResponse(e.getMessage());
        }
    }

    @GetMapping("/like/status/{articleId}")
    public ResponseEntity<?> getLikeStatus(@PathVariable Long articleId, Principal principal) {
        if (principal == null) {
            return unauthorizedResponse();
        }

        try {
            Long userId = Long.parseLong(principal.getName());
            Map<String, Object> data = new HashMap<>();
            data.put("liked", hasLiked(userId, articleId));
            data.put("likeCount", getArticleLikeCount(articleId));
            return successResponse("获取点赞状态成功", data);
        } catch (Exception e) {
            log.error("获取点赞状态失败: {}", e.getMessage(), e);
            return badRequestResponse(e.getMessage());
        }
    }

    @PostMapping("/collect/{articleId}")
    public ResponseEntity<?> collectArticle(@PathVariable Long articleId, Principal principal) {
        if (principal == null) {
            return unauthorizedResponse();
        }

        try {
            Long userId = Long.parseLong(principal.getName());
            QueryWrapper<UserArticleCollect> wrapper = new QueryWrapper<>();
            wrapper.eq("user_id", userId).eq("article_id", articleId);

            if (userArticleCollectMapper.selectOne(wrapper) == null) {
                UserArticleCollect collect = new UserArticleCollect();
                collect.setUserId(userId);
                collect.setArticleId(articleId);
                userArticleCollectMapper.insert(collect);
            }
            healthArticleService.syncArticleStats(articleId);

            Map<String, Object> data = new HashMap<>();
            data.put("collected", true);
            data.put("collectCount", getArticleCollectCount(articleId));
            return successResponse("收藏文章成功", data);
        } catch (Exception e) {
            log.error("收藏文章失败: {}", e.getMessage(), e);
            return badRequestResponse(e.getMessage());
        }
    }

    @DeleteMapping("/collect/{articleId}")
    public ResponseEntity<?> cancelCollectArticle(@PathVariable Long articleId, Principal principal) {
        if (principal == null) {
            return unauthorizedResponse();
        }

        try {
            Long userId = Long.parseLong(principal.getName());
            QueryWrapper<UserArticleCollect> wrapper = new QueryWrapper<>();
            wrapper.eq("user_id", userId).eq("article_id", articleId);
            userArticleCollectMapper.delete(wrapper);
            healthArticleService.syncArticleStats(articleId);

            Map<String, Object> data = new HashMap<>();
            data.put("collected", false);
            data.put("collectCount", getArticleCollectCount(articleId));
            return successResponse("已取消收藏", data);
        } catch (Exception e) {
            log.error("取消收藏文章失败: {}", e.getMessage(), e);
            return badRequestResponse(e.getMessage());
        }
    }

    @GetMapping("/collect/status/{articleId}")
    public ResponseEntity<?> getCollectStatus(@PathVariable Long articleId, Principal principal) {
        if (principal == null) {
            return unauthorizedResponse();
        }

        try {
            Long userId = Long.parseLong(principal.getName());
            Map<String, Object> data = new HashMap<>();
            data.put("collected", hasCollected(userId, articleId));
            data.put("collectCount", getArticleCollectCount(articleId));
            return successResponse("获取收藏状态成功", data);
        } catch (Exception e) {
            log.error("获取收藏状态失败: {}", e.getMessage(), e);
            return badRequestResponse(e.getMessage());
        }
    }

    @GetMapping("/collect/list")
    public ResponseEntity<?> getCollectedArticles(Principal principal) {
        if (principal == null) {
            return unauthorizedResponse();
        }

        try {
            Long userId = Long.parseLong(principal.getName());
            QueryWrapper<UserArticleCollect> wrapper = new QueryWrapper<>();
            wrapper.eq("user_id", userId).orderByDesc("create_time");

            List<Map<String, Object>> articles = userArticleCollectMapper.selectList(wrapper).stream()
                .map(item -> healthArticleService.getArticleById(item.getArticleId()))
                .filter(item -> item != null)
                .map(article -> toArticleView(article, userId))
                .collect(Collectors.toList());
            return successResponse("获取收藏文章成功", articles);
        } catch (Exception e) {
            log.error("获取收藏文章失败: {}", e.getMessage(), e);
            return badRequestResponse(e.getMessage());
        }
    }

    @GetMapping("/comment/list/{articleId}")
    public ResponseEntity<?> getArticleComments(@PathVariable Long articleId) {
        try {
            List<Map<String, Object>> comments = buildCommentTree(articleCommentMapper.selectByArticleId(articleId));
            return successResponse("获取评论成功", comments);
        } catch (Exception e) {
            log.error("获取评论失败: {}", e.getMessage(), e);
            return badRequestResponse(e.getMessage());
        }
    }

    @PostMapping("/comment/{articleId}")
    public ResponseEntity<?> addArticleComment(
        @PathVariable Long articleId,
        @RequestBody Map<String, Object> payload,
        Principal principal
    ) {
        if (principal == null) {
            return unauthorizedResponse();
        }

        try {
            String content = payload == null ? null : String.valueOf(payload.get("content"));
            if (!StringUtils.hasText(content)) {
                return badRequestResponse("评论内容不能为空");
            }

            Long parentId = parseLongValue(payload == null ? null : payload.get("parentId"));
            Long replyToUserId = parseLongValue(payload == null ? null : payload.get("replyToUserId"));

            if (parentId != null) {
                ArticleComment parentComment = articleCommentMapper.selectById(parentId);
                if (parentComment == null || Integer.valueOf(1).equals(parentComment.getIsDeleted())) {
                    return badRequestResponse("回复的评论不存在");
                }
                if (!articleId.equals(parentComment.getArticleId())) {
                    return badRequestResponse("评论所属文章不匹配");
                }
                if (replyToUserId == null) {
                    replyToUserId = parentComment.getUserId();
                }
            }

            ArticleComment comment = new ArticleComment();
            comment.setArticleId(articleId);
            comment.setUserId(Long.parseLong(principal.getName()));
            comment.setParentId(parentId);
            comment.setReplyToUserId(replyToUserId);
            comment.setContent(content.trim());
            comment.setIsDeleted(0);
            comment.setCreateTime(LocalDateTime.now());
            comment.setUpdateTime(LocalDateTime.now());
            articleCommentMapper.insert(comment);
            healthArticleService.syncArticleStats(articleId);

            return successResponse("评论成功", toCommentView(comment));
        } catch (Exception e) {
            log.error("发表评论失败: {}", e.getMessage(), e);
            return badRequestResponse(e.getMessage());
        }
    }

    @PostMapping("/publish")
    public ResponseEntity<?> publishArticle(@RequestBody HealthArticle article, Principal principal) {
        if (principal == null) {
            return unauthorizedResponse();
        }

        try {
            if (article == null) {
                return badRequestResponse("文章信息不能为空");
            }
            if (!StringUtils.hasText(article.getTitle())) {
                return badRequestResponse("文章标题不能为空");
            }
            if (!StringUtils.hasText(article.getContent())) {
                return badRequestResponse("文章内容不能为空");
            }

            User user = userService.findById(Long.parseLong(principal.getName()));
            if (user == null) {
                return unauthorizedResponse();
            }

            article.setId(null);
            article.setAuthor(StringUtils.hasText(article.getAuthor()) ? article.getAuthor().trim() : user.getUsername());
            article.setCategory(StringUtils.hasText(article.getCategory()) ? article.getCategory().trim() : "健康知识");
            article.setStatus(1);

            HealthArticle savedArticle = healthArticleService.saveArticle(article);
            return successResponse("发布文章成功", toArticleView(savedArticle, user.getId()));
        } catch (Exception e) {
            log.error("发布文章失败: {}", e.getMessage(), e);
            return badRequestResponse(e.getMessage());
        }
    }

    @DeleteMapping("/comment/{commentId}")
    public ResponseEntity<?> deleteArticleComment(@PathVariable Long commentId, Principal principal) {
        if (principal == null) {
            return unauthorizedResponse();
        }

        try {
            ArticleComment comment = articleCommentMapper.selectById(commentId);
            if (comment == null || Integer.valueOf(1).equals(comment.getIsDeleted())) {
                return badRequestResponse("评论不存在");
            }

            Long userId = Long.parseLong(principal.getName());
            User user = userService.findById(userId);
            if (!userId.equals(comment.getUserId()) && !userService.isAdmin(user)) {
                return badRequestResponse("无权删除该评论");
            }

            UpdateWrapper<ArticleComment> wrapper = new UpdateWrapper<>();
            wrapper.eq("id", commentId).set("is_deleted", 1);
            articleCommentMapper.update(null, wrapper);
            healthArticleService.syncArticleStats(comment.getArticleId());
            return successResponse("删除评论成功", true);
        } catch (Exception e) {
            log.error("删除评论失败: {}", e.getMessage(), e);
            return badRequestResponse(e.getMessage());
        }
    }

    @GetMapping("/admin/collect-stats")
    public ResponseEntity<?> getArticleCollectStats(Principal principal) {
        try {
            requireAdmin(principal);
            List<Map<String, Object>> stats = healthArticleService.getAllArticles().stream()
                .map(article -> {
                    Map<String, Object> item = new HashMap<>();
                    item.put("id", article.getId());
                    item.put("title", article.getTitle());
                    item.put("category", article.getCategory());
                    item.put("collectCount", getArticleCollectCount(article.getId()));
                    return item;
                })
                .sorted((left, right) -> Integer.compare(
                    (Integer) right.get("collectCount"),
                    (Integer) left.get("collectCount")
                ))
                .collect(Collectors.toList());
            return successResponse("获取文章收藏热度成功", stats);
        } catch (Exception e) {
            log.error("获取文章收藏热度失败: {}", e.getMessage(), e);
            return badRequestResponse(e.getMessage());
        }
    }

    @PostMapping("/save")
    public ResponseEntity<?> saveArticle(@RequestBody HealthArticle article, Principal principal) {
        try {
            requireAdmin(principal);
            return successResponse("保存文章成功", toArticleView(healthArticleService.saveArticle(article), null));
        } catch (Exception e) {
            log.error("保存文章失败: {}", e.getMessage(), e);
            return badRequestResponse(e.getMessage());
        }
    }

    @PutMapping("/update")
    public ResponseEntity<?> updateArticle(@RequestBody HealthArticle article, Principal principal) {
        try {
            requireAdmin(principal);
            return successResponse("更新文章成功", toArticleView(healthArticleService.updateArticle(article), null));
        } catch (Exception e) {
            log.error("更新文章失败: {}", e.getMessage(), e);
            return badRequestResponse(e.getMessage());
        }
    }

    @DeleteMapping("/delete/{articleId}")
    public ResponseEntity<?> deleteArticle(@PathVariable Long articleId, Principal principal) {
        try {
            requireAdmin(principal);
            boolean deleted = healthArticleService.deleteArticle(articleId);
            return successResponse(deleted ? "删除文章成功" : "文章不存在", deleted);
        } catch (Exception e) {
            log.error("删除文章失败: {}", e.getMessage(), e);
            return badRequestResponse(e.getMessage());
        }
    }

    private List<HealthArticle> queryArticles(String category, String tag, String keyword, String sort) {
        List<HealthArticle> articles;
        if (keyword != null && !keyword.trim().isEmpty()) {
            articles = healthArticleService.searchArticles(keyword.trim());
        } else if (tag != null && !tag.trim().isEmpty()) {
            articles = healthArticleService.getArticlesByTag(tag.trim());
        } else if (category != null && !category.trim().isEmpty()) {
            articles = healthArticleService.getArticlesByCategory(category.trim());
        } else {
            articles = healthArticleService.getLatestArticles(Integer.MAX_VALUE);
        }

        sortArticles(articles, sort);
        return articles;
    }

    private void sortArticles(List<HealthArticle> articles, String sort) {
        String sortKey = sort == null ? "recommend" : sort.toLowerCase(Locale.ROOT);
        if ("hot".equals(sortKey)) {
            articles.sort(Comparator.comparingInt(this::articleHeat).reversed());
            return;
        }
        articles.sort(Comparator.comparing(
            HealthArticle::getPublishDate,
            Comparator.nullsLast(Comparator.reverseOrder())
        ));
    }

    private List<HealthArticle> paginate(List<HealthArticle> source, Integer page, Integer pageSize) {
        int currentPage = page == null || page < 1 ? 1 : page;
        int size = pageSize == null || pageSize < 1 ? source.size() : pageSize;
        int start = (currentPage - 1) * size;
        if (start >= source.size()) {
            return new ArrayList<>();
        }
        int end = Math.min(start + size, source.size());
        return new ArrayList<>(source.subList(start, end));
    }

    private List<String> buildTagList() {
        Map<String, Integer> tagCountMap = new LinkedHashMap<>();
        for (HealthArticle article : healthArticleService.getLatestArticles(Integer.MAX_VALUE)) {
            for (String tag : parseTags(article.getTags())) {
                tagCountMap.put(tag, tagCountMap.getOrDefault(tag, 0) + 1);
            }
        }
        return tagCountMap.entrySet().stream()
            .sorted((left, right) -> Integer.compare(right.getValue(), left.getValue()))
            .map(Map.Entry::getKey)
            .collect(Collectors.toList());
    }

    private List<String> parseTags(String source) {
        if (source == null || source.trim().isEmpty()) {
            return new ArrayList<>();
        }

        String normalized = source.replace("[", "").replace("]", "").replace("\"", "");
        List<String> tags = new ArrayList<>();
        for (String item : normalized.split("[,，、;；/|\\s]+")) {
            String value = item.trim();
            if (!value.isEmpty()) {
                tags.add(value);
            }
        }
        return tags;
    }

    private Map<String, Object> toArticleView(HealthArticle article, Long userId) {
        Map<String, Object> data = new HashMap<>();
        int collectCount = getArticleCollectCount(article.getId());
        int likeCount = getArticleLikeCount(article.getId());
        int commentCount = getArticleCommentCount(article.getId());
        User authorUser = findUserByUsername(article.getAuthor());

        data.put("id", article.getId() == null ? null : String.valueOf(article.getId()));
        data.put("title", article.getTitle());
        data.put("summary", article.getSummary());
        data.put("content", article.getContent());
        data.put("category", article.getCategory());
        data.put("tags", article.getTags());
        data.put("author", article.getAuthor());
        data.put("authorAvatar", authorUser == null ? null : authorUser.getAvatar());
        data.put("suitableFor", article.getSuitableFor());
        data.put("goalType", article.getGoalType());
        data.put("readCount", article.getReadCount() == null ? 0 : article.getReadCount());
        data.put("likeCount", likeCount);
        data.put("commentCount", commentCount);
        data.put("shareCount", 0);
        data.put("collectCount", collectCount);
        data.put("publishDate", article.getPublishDate());
        data.put("createTime", article.getCreateTime());
        data.put("updateTime", article.getUpdateTime());
        data.put("status", article.getStatus());
        data.put("liked", userId != null && hasLiked(userId, article.getId()));
        data.put("collected", userId != null && hasCollected(userId, article.getId()));
        data.put("recommendReason", article.getRecommendReason());
        return data;
    }

    private User findUserByUsername(String username) {
        if (!StringUtils.hasText(username)) {
            return null;
        }

        return userService.listUsers().stream()
            .filter(item -> username.trim().equals(item.getUsername()))
            .findFirst()
            .orElse(null);
    }

    private Map<String, Object> toCommentView(ArticleComment comment) {
        Map<String, Object> data = new HashMap<>();
        User user = userService.findById(comment.getUserId());
        String username = user == null ? "匿名用户" : user.getUsername();
        User replyUser = comment.getReplyToUserId() == null ? null : userService.findById(comment.getReplyToUserId());
        data.put("id", comment.getId() == null ? null : String.valueOf(comment.getId()));
        data.put("articleId", comment.getArticleId() == null ? null : String.valueOf(comment.getArticleId()));
        data.put("userId", comment.getUserId() == null ? null : String.valueOf(comment.getUserId()));
        data.put("username", username);
        data.put("avatar", user == null ? null : user.getAvatar());
        data.put("parentId", comment.getParentId() == null ? null : String.valueOf(comment.getParentId()));
        data.put("replyToUserId", comment.getReplyToUserId() == null ? null : String.valueOf(comment.getReplyToUserId()));
        data.put("replyToUsername", replyUser == null ? null : replyUser.getUsername());
        data.put("content", comment.getContent());
        data.put("createTime", comment.getCreateTime());
        data.put("updateTime", comment.getUpdateTime());
        return data;
    }

    private List<Map<String, Object>> buildCommentTree(List<ArticleComment> comments) {
        Map<Long, Map<String, Object>> commentMap = new HashMap<>();
        List<Map<String, Object>> roots = new ArrayList<>();

        for (ArticleComment comment : comments) {
            Map<String, Object> view = toCommentView(comment);
            view.put("replies", new ArrayList<Map<String, Object>>());
            commentMap.put(comment.getId(), view);
        }

        for (ArticleComment comment : comments) {
            Map<String, Object> view = commentMap.get(comment.getId());
            if (comment.getParentId() == null) {
                roots.add(view);
                continue;
            }

            Map<String, Object> parent = commentMap.get(comment.getParentId());
            if (parent == null) {
                roots.add(view);
                continue;
            }

            @SuppressWarnings("unchecked")
            List<Map<String, Object>> replies = (List<Map<String, Object>>) parent.get("replies");
            replies.add(view);
        }

        return roots;
    }

    private Long parseLongValue(Object value) {
        if (value == null) {
            return null;
        }
        String text = String.valueOf(value).trim();
        if (!StringUtils.hasText(text) || "null".equalsIgnoreCase(text)) {
            return null;
        }
        return Long.parseLong(text);
    }

    private Integer parseIntegerValue(Object value) {
        if (value == null) {
            return null;
        }
        String text = String.valueOf(value).trim();
        if (!StringUtils.hasText(text) || "null".equalsIgnoreCase(text)) {
            return null;
        }
        return Integer.parseInt(text);
    }

    private int articleHeat(HealthArticle article) {
        int readCount = article.getReadCount() == null ? 0 : article.getReadCount();
        int likeCount = getArticleLikeCount(article.getId());
        int collectCount = getArticleCollectCount(article.getId());
        int commentCount = getArticleCommentCount(article.getId());
        return readCount + likeCount * 3 + collectCount * 4 + commentCount * 2;
    }

    private int getArticleCollectCount(Long articleId) {
        QueryWrapper<UserArticleCollect> wrapper = new QueryWrapper<>();
        wrapper.eq("article_id", articleId);
        return Math.toIntExact(userArticleCollectMapper.selectCount(wrapper));
    }

    private int getArticleLikeCount(Long articleId) {
        QueryWrapper<UserArticleLike> wrapper = new QueryWrapper<>();
        wrapper.eq("article_id", articleId);
        return Math.toIntExact(userArticleLikeMapper.selectCount(wrapper));
    }

    private int getArticleCommentCount(Long articleId) {
        QueryWrapper<ArticleComment> wrapper = new QueryWrapper<>();
        wrapper.eq("article_id", articleId).eq("is_deleted", 0);
        return Math.toIntExact(articleCommentMapper.selectCount(wrapper));
    }

    private boolean hasLiked(Long userId, Long articleId) {
        QueryWrapper<UserArticleLike> wrapper = new QueryWrapper<>();
        wrapper.eq("user_id", userId).eq("article_id", articleId);
        return userArticleLikeMapper.selectCount(wrapper) > 0;
    }

    private boolean hasCollected(Long userId, Long articleId) {
        QueryWrapper<UserArticleCollect> wrapper = new QueryWrapper<>();
        wrapper.eq("user_id", userId).eq("article_id", articleId);
        return userArticleCollectMapper.selectCount(wrapper) > 0;
    }

    private Long resolveUserId(Principal principal) {
        return principal == null ? null : Long.parseLong(principal.getName());
    }

    private void requireAdmin(Principal principal) {
        if (principal == null) {
            throw new RuntimeException("未登录或登录已过期");
        }
        User user = userService.findById(Long.parseLong(principal.getName()));
        if (!userService.isAdmin(user)) {
            throw new RuntimeException("仅管理员可执行该操作");
        }
    }

    private ResponseEntity<?> successResponse(String message, Object data) {
        Map<String, Object> response = new HashMap<>();
        response.put("code", 200);
        response.put("message", message);
        response.put("data", data);
        return ResponseEntity.ok(response);
    }

    private ResponseEntity<Map<String, Object>> unauthorizedResponse() {
        Map<String, Object> response = new HashMap<>();
        response.put("code", 401);
        response.put("message", "未登录或登录已过期");
        return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(response);
    }

    private ResponseEntity<Map<String, Object>> badRequestResponse(String message) {
        Map<String, Object> response = new HashMap<>();
        response.put("code", 400);
        response.put("message", message);
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
    }
}
