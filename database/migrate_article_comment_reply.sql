ALTER TABLE `article_comment`
ADD COLUMN `parent_id` bigint(20) NULL DEFAULT NULL COMMENT '父评论ID，空表示一级评论' AFTER `user_id`,
ADD COLUMN `reply_to_user_id` bigint(20) NULL DEFAULT NULL COMMENT '回复目标用户ID' AFTER `parent_id`;

ALTER TABLE `article_comment`
ADD KEY `idx_article_comment_parent` (`parent_id`);

ALTER TABLE `article_comment`
ADD CONSTRAINT `article_comment_ibfk_3` FOREIGN KEY (`parent_id`) REFERENCES `article_comment` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
ADD CONSTRAINT `article_comment_ibfk_4` FOREIGN KEY (`reply_to_user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;
