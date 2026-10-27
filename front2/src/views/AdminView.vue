<template>
  <div class="page-shell">
    <header class="page-head reveal">
      <div>
        <p class="eyebrow">Admin Console · 运营视图</p>
        <h1 class="page-title">管理后台</h1>
        <p class="page-sub">数据截至 2026-10-23 14:20 · 全站用户、内容与 AI 调用概览</p>
      </div>
      <div class="page-actions">
        <button class="btn btn-outline" @click="toast('报表已生成（演示环境不产生文件）')">
          <SvgIcon name="file-text" />导出报表
        </button>
        <button class="btn btn-primary" @click="publishOpen = true">
          <SvgIcon name="bell" />发布通知
        </button>
      </div>
    </header>

    <!-- ================= 概览 KPI ================= -->
    <section class="admin-top reveal d1">
      <template v-if="!overview">
        <article v-for="n in 4" :key="n" class="card stat-card">
          <span class="sk" style="height: 10px; width: 50%"></span>
          <span class="sk" style="height: 26px; width: 70%"></span>
        </article>
      </template>
      <template v-else>
        <article v-for="c in cards" :key="c.label" class="card stat-card">
          <div class="row-between">
            <span class="label">{{ c.label }}</span>
            <span class="q-ico">
              <SvgIcon :name="c.icon" />
            </span>
          </div>
          <div class="value">{{ c.value }}</div>
          <div class="delta" :class="{ down: c.down }">
            <SvgIcon :name="c.down ? 'trend-down' : 'trend-up'" />{{ c.delta }}
          </div>
        </article>
      </template>
    </section>

    <!-- ================= 趋势图 + 最近动态 ================= -->
    <section class="grid split mt-24">
      <article class="card reveal d2">
        <div class="card-hd">
          <h3>近 7 日活跃与记录</h3>
          <div class="chart-legend">
            <span><i></i>活跃用户</span>
            <span><i class="amber"></i>饮食记录</span>
          </div>
        </div>
        <div class="card-bd">
          <div class="chart-box">
            <svg
              v-if="chart"
              class="admin-chart"
              viewBox="0 0 760 260"
              role="img"
              aria-label="近 7 日活跃用户与饮食记录趋势"
            >
              <defs>
                <linearGradient id="adminGUsers" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="#1e6b52" stop-opacity=".18" />
                  <stop offset="100%" stop-color="#1e6b52" stop-opacity="0" />
                </linearGradient>
              </defs>
              <template v-for="g in chart.grid" :key="'g' + g.y">
                <line :x1="34" :y1="g.y" :x2="742" :y2="g.y" stroke="#eceae1" stroke-width="1" />
                <text :x="26" :y="g.y + 4" text-anchor="end" font-size="10" fill="#9aa39a">{{ g.label }}</text>
              </template>
              <path :d="chart.area" fill="url(#adminGUsers)" />
              <path
                :d="chart.usersPath"
                fill="none"
                stroke="#1e6b52"
                stroke-width="2.2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
              <path
                :d="chart.recordsPath"
                fill="none"
                stroke="#cf7c2e"
                stroke-width="2"
                stroke-dasharray="5 4"
                stroke-linecap="round"
              />
              <circle
                v-for="(p, i) in chart.dotsU"
                :key="'u' + i"
                :cx="p.cx"
                :cy="p.cy"
                r="3.5"
                fill="#1e6b52"
                stroke="#fff"
                stroke-width="2"
              />
              <circle
                v-for="(p, i) in chart.dotsR"
                :key="'r' + i"
                :cx="p.cx"
                :cy="p.cy"
                r="3.5"
                fill="#cf7c2e"
                stroke="#fff"
                stroke-width="2"
              />
              <text
                v-for="(l, i) in chart.labels"
                :key="'l' + i"
                :x="l.x"
                y="248"
                text-anchor="middle"
                font-size="10"
                fill="#9aa39a"
              >
                {{ l.text }}
              </text>
            </svg>
          </div>
          <div class="row-between small muted mt-12">
            <span>日均活跃 <b class="num">{{ chart ? num(chart.avgDau) : '—' }}</b></span>
            <span>日均记录 <b class="num">{{ chart ? num(chart.avgRecords) : '—' }}</b></span>
            <span>AI 调用成功率 <b class="num">98.4%</b></span>
          </div>
        </div>
      </article>

      <aside class="card reveal d3">
        <div class="card-hd">
          <h3>最近动态</h3>
          <span class="size small muted">实时</span>
        </div>
        <div class="card-bd">
          <div
            v-for="(a, i) in overview?.activities || []"
            :key="i"
            class="activity-row"
          >
            <span class="dot" :class="a.type === 'amber' ? 'amber' : a.type === 'gray' ? 'gray' : ''"></span>
            <span class="grow">{{ a.text }}</span>
            <time>{{ a.time }}</time>
          </div>
        </div>
      </aside>
    </section>

    <!-- ================= 热门榜单 ================= -->
    <section class="grid split-even mt-24">
      <article class="card reveal d4">
        <div class="card-hd">
          <h3>热门食谱 Top 5</h3>
          <RouterLink class="link-btn" to="/recipes">查看全部 <SvgIcon name="chevron-right" /></RouterLink>
        </div>
        <div class="card-bd">
          <div v-for="(r, i) in overview?.topRecipes || []" :key="r.id" class="rank-row">
            <span class="rank">{{ i + 1 }}</span>
            <span class="rank-name">{{ r.name }}</span>
            <span class="rank-val">{{ num(r.views) }} 浏览</span>
          </div>
        </div>
      </article>
      <article class="card reveal d5">
        <div class="card-hd">
          <h3>热门文章 Top 5</h3>
          <RouterLink class="link-btn" to="/knowledge">查看全部 <SvgIcon name="chevron-right" /></RouterLink>
        </div>
        <div class="card-bd">
          <div v-for="(a, i) in overview?.topArticles || []" :key="a.id" class="rank-row">
            <span class="rank">{{ i + 1 }}</span>
            <span class="rank-name">{{ a.title }}</span>
            <span class="rank-val">{{ num(a.views) }} 阅读</span>
          </div>
        </div>
      </article>
    </section>

    <!-- ================= 内容 / 用户管理 ================= -->
    <section class="card mt-24 reveal d6">
      <div class="card-hd admin-tabs-hd">
        <div class="seg">
          <button type="button" :class="{ on: tab === 'users' }" @click="pickTab('users')">
            <SvgIcon name="users" />用户管理
          </button>
          <button type="button" :class="{ on: tab === 'recipe' }" @click="pickTab('recipe')">
            <SvgIcon name="book-open" />食谱管理
          </button>
          <button type="button" :class="{ on: tab === 'article' }" @click="pickTab('article')">
            <SvgIcon name="news" />文章管理
          </button>
          <button type="button" :class="{ on: tab === 'ingredient' }" @click="pickTab('ingredient')">
            <SvgIcon name="apple" />食材管理
          </button>
        </div>
        <span class="size small muted">演示数据</span>
      </div>

      <!-- ---------- 用户 ---------- -->
      <div v-show="tab === 'users'" class="admin-panel">
        <div class="admin-toolbar">
          <div class="search-box">
            <SvgIcon name="search" />
            <input v-model="userKeyword" class="input" placeholder="搜索用户名或邮箱" @input="onUserSearch" />
          </div>
          <select v-model="goalFilter" class="select" style="width: 120px; height: 36px">
            <option value="">全部目标</option>
            <option>减脂</option>
            <option>增肌</option>
            <option>控糖</option>
            <option>维持</option>
          </select>
        </div>
        <div class="table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th>用户</th>
                <th>目标</th>
                <th>记录数</th>
                <th>注册时间</th>
                <th>状态</th>
                <th style="text-align: right">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!users.length">
                <td colspan="6">
                  <div class="empty">
                    <div class="empty-ico"><SvgIcon name="users" /></div>
                    <h4>没有匹配的用户</h4>
                    <p>换个关键词或筛选条件试试。</p>
                  </div>
                </td>
              </tr>
              <tr v-for="u in users" :key="u.id" :class="{ disabled: !u.status }">
                <td>
                  <div class="user-cell">
                    <span class="avatar sm">{{ u.name[0] }}</span>
                    <div>
                      <strong>{{ u.name }}</strong>
                      <span>{{ u.email }}</span>
                    </div>
                  </div>
                </td>
                <td><span class="tag">{{ u.goal }}</span></td>
                <td class="num">{{ u.records }}</td>
                <td class="num">{{ u.joined }}</td>
                <td>
                  <span class="status-dot" :class="{ off: !u.status }"><i></i>{{ u.status ? '正常' : '已禁用' }}</span>
                </td>
                <td style="text-align: right">
                  <button
                    class="btn btn-sm"
                    :class="u.status ? 'btn-danger' : 'btn-soft'"
                    @click="toggleUser(u)"
                  >
                    {{ u.status ? '禁用' : '启用' }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="card-ft row-between">
          <span class="small muted">共 {{ users.length }} 位用户</span>
          <div class="row">
            <button class="btn btn-outline btn-sm" @click="toast('已经是第一页')">上一页</button>
            <span class="small muted">第 1 / 1 页</span>
            <button class="btn btn-outline btn-sm" @click="toast('已经是最后一页')">下一页</button>
          </div>
        </div>
      </div>

      <!-- ---------- 食谱 ---------- -->
      <div v-show="tab === 'recipe'" class="admin-panel">
        <div class="admin-toolbar">
          <div class="search-box">
            <SvgIcon name="search" />
            <input
              v-model="content.recipe.keyword"
              class="input"
              placeholder="搜索食谱名称"
              @input="onContentSearch('recipe')"
            />
          </div>
          <select
            v-model="content.recipe.cat"
            class="select"
            style="width: 120px; height: 36px"
            @change="loadContent('recipe')"
          >
            <option value="">全部餐次</option>
            <option>早餐</option>
            <option>午餐</option>
            <option>晚餐</option>
            <option>加餐</option>
          </select>
          <select
            v-model="content.recipe.status"
            class="select"
            style="width: 112px; height: 36px"
            @change="loadContent('recipe')"
          >
            <option value="">全部状态</option>
            <option value="on">已上架</option>
            <option value="off">已下架</option>
          </select>
          <button class="btn btn-primary btn-sm" @click="openContentModal('recipe', null)">
            <SvgIcon name="plus" />新建食谱
          </button>
        </div>
        <div class="table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th>食谱</th>
                <th>餐次</th>
                <th>热量</th>
                <th>适宜目标</th>
                <th>浏览</th>
                <th>状态</th>
                <th style="text-align: right">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!contentView.recipe.rows.length">
                <td colspan="7">
                  <div class="empty">
                    <div class="empty-ico"><SvgIcon name="book-open" /></div>
                    <h4>还没有食谱</h4>
                    <p>点击「新建食谱」创建第一条内容。</p>
                  </div>
                </td>
              </tr>
              <tr v-for="x in contentView.recipe.rows" :key="x.id" :class="{ off: x.status === 0 }">
                <td>
                  <div class="content-cell">
                    <span class="thumb"><img :src="x.img" alt="" /></span>
                    <div>
                      <strong>{{ x.name }}</strong>
                      <span class="sub">{{ x.desc }}</span>
                    </div>
                  </div>
                </td>
                <td><span class="tag">{{ x.mealType }}</span></td>
                <td class="num">{{ num(x.kcal) }}</td>
                <td>
                  <div class="row wrap" style="gap: 4px">
                    <span v-for="f in x.fit || []" :key="f" class="tag">{{ f }}</span>
                  </div>
                </td>
                <td class="num">{{ num(x.views || 0) }}</td>
                <td>
                  <span class="status-dot" :class="{ off: x.status === 0 }">
                    <i></i>{{ x.status === 0 ? '已下架' : '已上架' }}
                  </span>
                </td>
                <td style="text-align: right">
                  <div class="row" style="justify-content: flex-end; gap: 6px">
                    <button class="btn btn-outline btn-sm" @click="openContentModal('recipe', x)">编辑</button>
                    <button
                      class="btn btn-sm"
                      :class="x.status === 0 ? 'btn-danger' : 'btn-soft'"
                      @click="toggleContent('recipe', x)"
                    >
                      {{ x.status === 0 ? '上架' : '下架' }}
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="card-ft row-between">
          <span class="small muted">共 {{ content.recipe.list.length }} 条 · 每页 {{ PAGE_SIZE }} 条</span>
          <div class="row">
            <button
              class="btn btn-outline btn-sm"
              :disabled="contentView.recipe.page <= 1"
              @click="goPage('recipe', -1)"
            >
              上一页
            </button>
            <span class="small muted">第 {{ contentView.recipe.page }} / {{ contentView.recipe.pages }} 页</span>
            <button
              class="btn btn-outline btn-sm"
              :disabled="contentView.recipe.page >= contentView.recipe.pages"
              @click="goPage('recipe', 1)"
            >
              下一页
            </button>
          </div>
        </div>
      </div>

      <!-- ---------- 文章 ---------- -->
      <div v-show="tab === 'article'" class="admin-panel">
        <div class="admin-toolbar">
          <div class="search-box">
            <SvgIcon name="search" />
            <input
              v-model="content.article.keyword"
              class="input"
              placeholder="搜索文章标题"
              @input="onContentSearch('article')"
            />
          </div>
          <select
            v-model="content.article.cat"
            class="select"
            style="width: 130px; height: 36px"
            @change="loadContent('article')"
          >
            <option value="">全部分类</option>
            <option>减肥指南</option>
            <option>饮食指南</option>
            <option>营养知识</option>
            <option>食品安全</option>
          </select>
          <select
            v-model="content.article.status"
            class="select"
            style="width: 112px; height: 36px"
            @change="loadContent('article')"
          >
            <option value="">全部状态</option>
            <option value="on">已发布</option>
            <option value="off">已下架</option>
          </select>
          <button class="btn btn-primary btn-sm" @click="openContentModal('article', null)">
            <SvgIcon name="plus" />新建文章
          </button>
        </div>
        <div class="table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th>文章</th>
                <th>分类</th>
                <th>作者</th>
                <th>浏览</th>
                <th>状态</th>
                <th style="text-align: right">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!contentView.article.rows.length">
                <td colspan="6">
                  <div class="empty">
                    <div class="empty-ico"><SvgIcon name="news" /></div>
                    <h4>还没有文章</h4>
                    <p>点击「新建文章」发布第一篇内容。</p>
                  </div>
                </td>
              </tr>
              <tr v-for="x in contentView.article.rows" :key="x.id" :class="{ off: x.status === 0 }">
                <td>
                  <div class="content-cell">
                    <span class="thumb"><img :src="x.cover" alt="" /></span>
                    <div>
                      <strong>{{ x.title }}</strong>
                      <span class="sub">{{ x.summary }}</span>
                    </div>
                  </div>
                </td>
                <td><span class="tag">{{ x.cat }}</span></td>
                <td>{{ x.author }}</td>
                <td class="num">{{ num(x.views || 0) }}</td>
                <td>
                  <span class="status-dot" :class="{ off: x.status === 0 }">
                    <i></i>{{ x.status === 0 ? '已下架' : '已发布' }}
                  </span>
                </td>
                <td style="text-align: right">
                  <div class="row" style="justify-content: flex-end; gap: 6px">
                    <button class="btn btn-outline btn-sm" @click="openContentModal('article', x)">编辑</button>
                    <button
                      class="btn btn-sm"
                      :class="x.status === 0 ? 'btn-danger' : 'btn-soft'"
                      @click="toggleContent('article', x)"
                    >
                      {{ x.status === 0 ? '上架' : '下架' }}
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="card-ft row-between">
          <span class="small muted">共 {{ content.article.list.length }} 条 · 每页 {{ PAGE_SIZE }} 条</span>
          <div class="row">
            <button
              class="btn btn-outline btn-sm"
              :disabled="contentView.article.page <= 1"
              @click="goPage('article', -1)"
            >
              上一页
            </button>
            <span class="small muted">第 {{ contentView.article.page }} / {{ contentView.article.pages }} 页</span>
            <button
              class="btn btn-outline btn-sm"
              :disabled="contentView.article.page >= contentView.article.pages"
              @click="goPage('article', 1)"
            >
              下一页
            </button>
          </div>
        </div>
      </div>

      <!-- ---------- 食材 ---------- -->
      <div v-show="tab === 'ingredient'" class="admin-panel">
        <div class="admin-toolbar">
          <div class="search-box">
            <SvgIcon name="search" />
            <input
              v-model="content.ingredient.keyword"
              class="input"
              placeholder="搜索食材名称"
              @input="onContentSearch('ingredient')"
            />
          </div>
          <select
            v-model="content.ingredient.cat"
            class="select"
            style="width: 130px; height: 36px"
            @change="loadContent('ingredient')"
          >
            <option value="">全部分类</option>
            <option>肉类</option>
            <option>蛋类</option>
            <option>豆制品</option>
            <option>主食</option>
            <option>蔬菜</option>
            <option>水果</option>
            <option>乳制品</option>
            <option>坚果</option>
          </select>
          <select
            v-model="content.ingredient.status"
            class="select"
            style="width: 112px; height: 36px"
            @change="loadContent('ingredient')"
          >
            <option value="">全部状态</option>
            <option value="on">已上架</option>
            <option value="off">已下架</option>
          </select>
          <button class="btn btn-primary btn-sm" @click="openContentModal('ingredient', null)">
            <SvgIcon name="plus" />新建食材
          </button>
        </div>
        <div class="table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th>食材</th>
                <th>分类</th>
                <th>热量</th>
                <th>蛋白</th>
                <th>碳水</th>
                <th>脂肪</th>
                <th>状态</th>
                <th style="text-align: right">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!contentView.ingredient.rows.length">
                <td colspan="8">
                  <div class="empty">
                    <div class="empty-ico"><SvgIcon name="apple" /></div>
                    <h4>还没有食材</h4>
                    <p>点击「新建食材」补充营养库。</p>
                  </div>
                </td>
              </tr>
              <tr v-for="x in contentView.ingredient.rows" :key="x.id" :class="{ off: x.status === 0 }">
                <td>
                  <div class="content-cell">
                    <span class="thumb">{{ (x.name || '').charAt(0) }}</span>
                    <div>
                      <strong>{{ x.name }}</strong>
                      <span class="sub">{{ x.desc || '' }}</span>
                    </div>
                  </div>
                </td>
                <td><span class="tag">{{ x.cat }}</span></td>
                <td class="num">{{ num(x.kcal) }}</td>
                <td class="num">{{ x.p }}g</td>
                <td class="num">{{ x.c }}g</td>
                <td class="num">{{ x.f }}g</td>
                <td>
                  <span class="status-dot" :class="{ off: x.status === 0 }">
                    <i></i>{{ x.status === 0 ? '已下架' : '已上架' }}
                  </span>
                </td>
                <td style="text-align: right">
                  <div class="row" style="justify-content: flex-end; gap: 6px">
                    <button class="btn btn-outline btn-sm" @click="openContentModal('ingredient', x)">编辑</button>
                    <button
                      class="btn btn-sm"
                      :class="x.status === 0 ? 'btn-danger' : 'btn-soft'"
                      @click="toggleContent('ingredient', x)"
                    >
                      {{ x.status === 0 ? '上架' : '下架' }}
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="card-ft row-between">
          <span class="small muted">共 {{ content.ingredient.list.length }} 条 · 每页 {{ PAGE_SIZE }} 条</span>
          <div class="row">
            <button
              class="btn btn-outline btn-sm"
              :disabled="contentView.ingredient.page <= 1"
              @click="goPage('ingredient', -1)"
            >
              上一页
            </button>
            <span class="small muted">第 {{ contentView.ingredient.page }} / {{ contentView.ingredient.pages }} 页</span>
            <button
              class="btn btn-outline btn-sm"
              :disabled="contentView.ingredient.page >= contentView.ingredient.pages"
              @click="goPage('ingredient', 1)"
            >
              下一页
            </button>
          </div>
        </div>
      </div>
    </section>

    <p class="small muted mt-32" style="text-align: center">
      后台数据为演示用假数据；真实实现需接入管理端鉴权、审计日志与内容审核流。
    </p>
  </div>

  <!-- ================= 发布通知 ================= -->
  <div class="overlay" :class="{ open: publishOpen }" @click.self="publishOpen = false">
    <div class="modal">
      <div class="modal-hd">
        <div>
          <h3>发布通知</h3>
          <p>面向全站或指定用户推送，发布后立即生效。</p>
        </div>
        <button class="modal-close" @click="publishOpen = false"><SvgIcon name="x" /></button>
      </div>
      <div class="modal-bd">
        <label class="field mb-16">
          <span class="field-label">通知类型</span>
          <select v-model="pub.type" class="select">
            <option>系统</option>
            <option>目标达成</option>
            <option>饮食提醒</option>
            <option>文章推荐</option>
            <option>警告</option>
          </select>
        </label>
        <label class="field mb-16">
          <span class="field-label">标题</span>
          <input v-model="pub.title" class="input" placeholder="例如：本周目标完成度 86%" />
        </label>
        <label class="field mb-16">
          <span class="field-label">内容</span>
          <textarea
            v-model="pub.content"
            class="textarea"
            placeholder="写清楚要提醒用户什么，以及下一步动作。"
          ></textarea>
        </label>
        <p class="field-label">发送范围</p>
        <div class="row wrap" style="gap: 16px">
          <label class="switch">
            <input v-model="pub.scope" type="radio" value="all" style="position: static; opacity: 1; width: auto; height: auto" />
            <span class="switch-text">全部启用用户</span>
          </label>
          <label class="switch">
            <input v-model="pub.scope" type="radio" value="one" style="position: static; opacity: 1; width: auto; height: auto" />
            <span class="switch-text">指定用户</span>
          </label>
        </div>
        <label class="field mt-12">
          <span class="field-label">指定用户 ID（选择「指定用户」时填写）</span>
          <input v-model="pub.userId" class="input" placeholder="例如：1024" :disabled="pub.scope !== 'one'" />
        </label>
      </div>
      <div class="modal-ft">
        <button class="btn btn-outline" @click="publishOpen = false">取消</button>
        <button class="btn btn-primary" :disabled="publishing" @click="confirmPublish">
          {{ publishing ? '发布中…' : '确认发布' }}
        </button>
      </div>
    </div>
  </div>

  <!-- ================= 内容编辑（食谱 / 文章 / 食材共用） ================= -->
  <div class="overlay" :class="{ open: contentOpen }" @click.self="contentOpen = false">
    <div class="modal">
      <div class="modal-hd">
        <div>
          <h3>{{ editing.id ? '编辑' : '新建' }}{{ TYPE_LABEL[editing.type] }}</h3>
          <p>{{ editing.id ? '修改后保存，前台内容会同步更新。' : '保存后立即同步到前台内容库。' }}</p>
        </div>
        <button class="modal-close" @click="contentOpen = false"><SvgIcon name="x" /></button>
      </div>
      <div class="modal-bd">
        <!-- 食谱 -->
        <div v-if="editing.type === 'recipe'">
          <label class="field mb-16">
            <span class="field-label">食谱名称</span>
            <input v-model="form.crName" class="input" placeholder="例如：香煎鸡胸藜麦碗" />
          </label>
          <div class="grid g2 mb-16" style="gap: 14px">
            <label class="field">
              <span class="field-label">餐次</span>
              <select v-model="form.crMeal" class="select">
                <option>早餐</option>
                <option>午餐</option>
                <option>晚餐</option>
                <option>加餐</option>
              </select>
            </label>
            <label class="field">
              <span class="field-label">菜系</span>
              <input v-model="form.crCuisine" class="input" placeholder="轻食 / 中式 / 西式" />
            </label>
            <label class="field">
              <span class="field-label">烹饪时长（分钟）</span>
              <input v-model="form.crTime" class="input" type="number" min="1" placeholder="25" />
            </label>
            <label class="field">
              <span class="field-label">总热量（kcal）</span>
              <input v-model="form.crKcal" class="input" type="number" min="0" placeholder="520" />
            </label>
            <label class="field">
              <span class="field-label">蛋白质（g）</span>
              <input v-model="form.crP" class="input" type="number" min="0" placeholder="42" />
            </label>
            <label class="field">
              <span class="field-label">碳水（g）</span>
              <input v-model="form.crC" class="input" type="number" min="0" placeholder="48" />
            </label>
            <label class="field">
              <span class="field-label">脂肪（g）</span>
              <input v-model="form.crF" class="input" type="number" min="0" placeholder="16" />
            </label>
            <label class="field">
              <span class="field-label">状态</span>
              <select v-model="form.crStatus" class="select">
                <option value="1">上架</option>
                <option value="0">下架</option>
              </select>
            </label>
          </div>
          <label class="field mb-16">
            <span class="field-label">简介</span>
            <textarea v-model="form.crDesc" class="textarea" placeholder="一句话说明这道菜适合谁、解决什么问题。"></textarea>
          </label>
          <p class="field-label mb-8">适宜目标</p>
          <div class="row wrap" style="gap: 8px">
            <button
              v-for="f in FIT_OPTIONS"
              :key="f"
              type="button"
              class="chip"
              :class="{ on: form.crFit.includes(f) }"
              @click="toggleFit(f)"
            >
              {{ f }}
            </button>
          </div>
        </div>

        <!-- 文章 -->
        <div v-else-if="editing.type === 'article'">
          <label class="field mb-16">
            <span class="field-label">文章标题</span>
            <input v-model="form.caTitle" class="input" placeholder="例如：减脂期怎么选主食" />
          </label>
          <div class="grid g2 mb-16" style="gap: 14px">
            <label class="field">
              <span class="field-label">分类</span>
              <select v-model="form.caCat" class="select">
                <option>减肥指南</option>
                <option>饮食指南</option>
                <option>营养知识</option>
                <option>食品安全</option>
              </select>
            </label>
            <label class="field">
              <span class="field-label">作者</span>
              <input v-model="form.caAuthor" class="input" placeholder="平台编辑部" />
            </label>
            <label class="field">
              <span class="field-label">标签（逗号分隔）</span>
              <input v-model="form.caTags" class="input" placeholder="低GI, 主食, 减脂" />
            </label>
            <label class="field">
              <span class="field-label">状态</span>
              <select v-model="form.caStatus" class="select">
                <option value="1">发布</option>
                <option value="0">下架</option>
              </select>
            </label>
          </div>
          <label class="field">
            <span class="field-label">摘要</span>
            <textarea v-model="form.caSummary" class="textarea" placeholder="用一两句话概括文章解决的问题。"></textarea>
          </label>
        </div>

        <!-- 食材 -->
        <div v-else>
          <label class="field mb-16">
            <span class="field-label">食材名称</span>
            <input v-model="form.ciName" class="input" placeholder="例如：芦笋" />
          </label>
          <div class="grid g2 mb-16" style="gap: 14px">
            <label class="field">
              <span class="field-label">分类</span>
              <select v-model="form.ciCat" class="select">
                <option>肉类</option>
                <option>蛋类</option>
                <option>豆制品</option>
                <option>主食</option>
                <option>蔬菜</option>
                <option>水果</option>
                <option>乳制品</option>
                <option>坚果</option>
              </select>
            </label>
            <label class="field">
              <span class="field-label">热量（kcal / 100g）</span>
              <input v-model="form.ciKcal" class="input" type="number" min="0" placeholder="20" />
            </label>
            <label class="field">
              <span class="field-label">蛋白质（g）</span>
              <input v-model="form.ciP" class="input" type="number" min="0" placeholder="2.2" />
            </label>
            <label class="field">
              <span class="field-label">碳水（g）</span>
              <input v-model="form.ciC" class="input" type="number" min="0" placeholder="3.9" />
            </label>
            <label class="field">
              <span class="field-label">脂肪（g）</span>
              <input v-model="form.ciF" class="input" type="number" min="0" placeholder="0.1" />
            </label>
            <label class="field">
              <span class="field-label">膳食纤维（g）</span>
              <input v-model="form.ciFiber" class="input" type="number" min="0" placeholder="2.1" />
            </label>
            <label class="field">
              <span class="field-label">状态</span>
              <select v-model="form.ciStatus" class="select">
                <option value="1">上架</option>
                <option value="0">下架</option>
              </select>
            </label>
          </div>
          <label class="field">
            <span class="field-label">简介</span>
            <textarea v-model="form.ciDesc" class="textarea" placeholder="说明营养特点与适用人群。"></textarea>
          </label>
        </div>
      </div>
      <div class="modal-ft">
        <button class="btn btn-outline" @click="contentOpen = false">取消</button>
        <button class="btn btn-primary" :disabled="saving" @click="saveContent">
          {{ saving ? '保存中…' : '保存' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
/* ============================================================
   AdminView · 管理后台
   ------------------------------------------------------------
   对应静态版 pages/admin.html，四块内容：
   1) 概览 KPI + 近 7 日趋势（SVG 手绘，和原版同一套坐标算法）
   2) 最近动态 + 热门食谱 / 文章 Top 5
   3) 用户管理（搜索、目标筛选、启用/禁用）
   4) 内容管理（食谱 / 文章 / 食材三个分栏，按需加载 + 分页）
   外加两个弹窗：发布通知、新建/编辑内容

   静态版靠 querySelector 逐个改 DOM；这里全部换成响应式状态，
   手风琴式「先 innerHTML 再 Icons.hydrate 再绑事件」的写法都不需要了。
   ============================================================ */
import { ref, reactive, computed, onMounted } from 'vue'
import { adminApi, notificationsApi } from '@/services/api'
import { useAppStore } from '@/stores/app'
import { toast } from '@/composables/useToast'
import { confirmDialog } from '@/composables/useConfirm'
import SvgIcon from '@/components/SvgIcon.vue'
import recipeChicken from '@/assets/recipe-chicken.jpg'
import articleVegetables from '@/assets/article-vegetables.jpg'

const store = useAppStore()

/* ---------------- 通用 ---------------- */
/** 千分位，对应静态版 UI.num() */
const num = (n) => Number(n || 0).toLocaleString('zh-CN')

/* ---------------- 概览 ---------------- */
const overview = ref(null)

const cards = computed(() => {
  const s = overview.value?.stats || {}
  return [
    { label: '累计用户', value: num(s.users), delta: '+3.2% 较上周', icon: 'users', down: false },
    { label: '今日活跃', value: num(s.dau), delta: '+6.8% 较昨日', icon: 'activity', down: false },
    { label: '今日记录', value: num(s.records), delta: '覆盖率 71%', icon: 'notebook', down: false },
    {
      label: '内容总量',
      value: num(s.recipes + s.articles + s.ingredients),
      delta: s.recipes + ' 食谱 · ' + s.articles + ' 文章 · ' + s.ingredients + ' 食材',
      icon: 'book-open',
      down: false
    }
  ]
})

/* 趋势图：坐标算法与静态版完全一致，只是把拼字符串换成绑属性 */
const W = 760
const H = 260
const PAD = { l: 34, r: 18, t: 20, b: 34 }

const chart = computed(() => {
  const data = overview.value?.trend || []
  if (!data.length) return null

  const iw = W - PAD.l - PAD.r
  const ih = H - PAD.t - PAD.b
  const maxU = Math.max(...data.map((x) => x.users)) * 1.25
  const maxR = Math.max(...data.map((x) => x.records)) * 1.25
  const x = (i) => PAD.l + (iw / (data.length - 1)) * i
  const yU = (v) => PAD.t + ih - (v / maxU) * ih
  const yR = (v) => PAD.t + ih - (v / maxR) * ih
  const poly = (key, fn) =>
    data.map((d, i) => (i ? 'L' : 'M') + x(i).toFixed(1) + ' ' + fn(d[key]).toFixed(1)).join(' ')

  const base = PAD.t + ih
  const area =
    poly('users', yU) + ' L' + x(data.length - 1) + ' ' + base + ' L' + PAD.l + ' ' + base + ' Z'

  const grid = []
  for (let i = 0; i <= 4; i++) {
    const y = PAD.t + (ih / 4) * i
    grid.push({ y, label: Math.round(maxU * (1 - i / 4)) })
  }

  return {
    grid,
    area,
    usersPath: poly('users', yU),
    recordsPath: poly('records', yR),
    dotsU: data.map((d, i) => ({ cx: x(i), cy: yU(d.users) })),
    dotsR: data.map((d, i) => ({ cx: x(i), cy: yR(d.records) })),
    labels: data.map((d, i) => ({ x: x(i), text: d.date })),
    avgDau: Math.round(data.reduce((a, b) => a + b.users, 0) / data.length),
    avgRecords: Math.round(data.reduce((a, b) => a + b.records, 0) / data.length)
  }
})

/* ---------------- 用户管理 ---------------- */
const users = ref([])
const userKeyword = ref('')
const goalFilter = ref('')
let userTimer = null

async function loadUsers() {
  const res = await adminApi.users({ keyword: userKeyword.value.trim() })
  if (res.code !== 200) return
  // 目标筛选在原版里也是前端过一遍，不动接口
  users.value = res.data.list.filter((u) => !goalFilter.value || u.goal === goalFilter.value)
}

function onUserSearch() {
  clearTimeout(userTimer)
  userTimer = setTimeout(loadUsers, 300)
}

async function toggleUser(u) {
  const on = !!u.status
  const ok = await confirmDialog('确定要' + (on ? '禁用' : '启用') + '用户「' + u.name + '」吗？', {
    title: on ? '禁用用户' : '启用用户',
    okText: '确定',
    danger: on
  })
  if (!ok) return
  const res = await adminApi.toggleUser(u.id, on ? 0 : 1)
  toast(res.message)
  loadUsers()
}

/* ---------------- 内容管理 ---------------- */
const PAGE_SIZE = 8
const TYPE_LABEL = { recipe: '食谱', article: '文章', ingredient: '食材' }
const FIT_OPTIONS = ['减脂', '增肌', '控糖', '维持']

const tab = ref('users')

const content = reactive({
  recipe: { list: [], page: 1, loaded: false, keyword: '', cat: '', status: '' },
  article: { list: [], page: 1, loaded: false, keyword: '', cat: '', status: '' },
  ingredient: { list: [], page: 1, loaded: false, keyword: '', cat: '', status: '' }
})

/** 每栏的分页切片 + 总页数，模板里直接读 */
const contentView = computed(() => {
  const out = {}
  for (const type of Object.keys(content)) {
    const st = content[type]
    const pages = Math.max(1, Math.ceil(st.list.length / PAGE_SIZE))
    const page = Math.min(st.page, pages)
    out[type] = {
      rows: st.list.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE),
      pages,
      page,
      total: st.list.length
    }
  }
  return out
})

async function loadContent(type) {
  const st = content[type]
  const res = await adminApi.contentList(type, {
    keyword: st.keyword.trim(),
    cat: st.cat,
    status: st.status
  })
  if (res.code !== 200) {
    toast(res.message, 'error')
    return
  }
  st.list = res.data.list
  st.loaded = true
  st.page = 1
}

const contentTimers = {}
function onContentSearch(type) {
  clearTimeout(contentTimers[type])
  contentTimers[type] = setTimeout(() => loadContent(type), 300)
}

function pickTab(key) {
  tab.value = key
  // 内容面板按需加载，和原版一致
  if (key !== 'users' && !content[key].loaded) loadContent(key)
}

function goPage(type, step) {
  const view = contentView.value[type]
  const next = view.page + step
  if (next < 1 || next > view.pages) return
  content[type].page = next
}

async function toggleContent(type, item) {
  const on = item.status !== 0
  const ok = await confirmDialog(
    '确定要' + (on ? '下架' : '上架') + '「' + (item.name || item.title) + '」吗？' + (on ? '下架后前台将不再展示。' : ''),
    { title: on ? '下架内容' : '上架内容', okText: '确定', danger: on }
  )
  if (!ok) return
  const res = await adminApi.contentToggle(type, item.id, on ? 0 : 1)
  toast(res.message)
  loadContent(type)
}

/* ---------------- 内容编辑弹窗 ---------------- */
const contentOpen = ref(false)
const saving = ref(false)
const editing = reactive({ type: 'recipe', id: 0 })

const form = reactive({
  // 食谱
  crName: '',
  crMeal: '午餐',
  crCuisine: '轻食',
  crTime: '',
  crKcal: '',
  crP: '',
  crC: '',
  crF: '',
  crDesc: '',
  crStatus: '1',
  crFit: ['减脂'],
  // 文章
  caTitle: '',
  caCat: '减肥指南',
  caAuthor: '平台编辑部',
  caTags: '',
  caStatus: '1',
  caSummary: '',
  // 食材
  ciName: '',
  ciCat: '蔬菜',
  ciKcal: '',
  ciP: '',
  ciC: '',
  ciF: '',
  ciFiber: '',
  ciStatus: '1',
  ciDesc: ''
})

const s = (v) => (v == null ? '' : String(v))

function openContentModal(type, item) {
  editing.type = type
  editing.id = item ? item.id : 0

  if (type === 'recipe') {
    form.crName = s(item?.name)
    form.crMeal = item?.mealType || '午餐'
    form.crCuisine = item?.cuisine || '轻食'
    form.crTime = s(item?.time)
    form.crKcal = s(item?.kcal)
    form.crP = s(item?.p)
    form.crC = s(item?.c)
    form.crF = s(item?.f)
    form.crDesc = s(item?.desc)
    form.crStatus = String(item && item.status === 0 ? 0 : 1)
    form.crFit = (item?.fit || ['减脂']).slice()
  } else if (type === 'article') {
    form.caTitle = s(item?.title)
    form.caCat = item?.cat || '减肥指南'
    form.caAuthor = item?.author || '平台编辑部'
    form.caTags = item ? (item.tags || []).join(', ') : ''
    form.caStatus = String(item && item.status === 0 ? 0 : 1)
    form.caSummary = s(item?.summary)
  } else {
    form.ciName = s(item?.name)
    form.ciCat = item?.cat || '蔬菜'
    form.ciKcal = s(item?.kcal)
    form.ciP = s(item?.p)
    form.ciC = s(item?.c)
    form.ciF = s(item?.f)
    form.ciFiber = s(item?.fiber)
    form.ciStatus = String(item && item.status === 0 ? 0 : 1)
    form.ciDesc = s(item?.desc)
  }

  contentOpen.value = true
}

function toggleFit(f) {
  const i = form.crFit.indexOf(f)
  if (i > -1) form.crFit.splice(i, 1)
  else form.crFit.push(f)
}

const n0 = (v) => Number(v) || 0

async function saveContent() {
  const type = editing.type
  const payload = {}
  if (editing.id) payload.id = editing.id

  if (type === 'recipe') {
    const name = form.crName.trim()
    if (!name) return toast('请填写食谱名称', 'error')
    if (!form.crFit.length) return toast('请至少选择一个适宜目标', 'error')
    Object.assign(payload, {
      name,
      mealType: form.crMeal,
      cuisine: form.crCuisine.trim() || '家常',
      time: n0(form.crTime),
      kcal: n0(form.crKcal),
      p: n0(form.crP),
      c: n0(form.crC),
      f: n0(form.crF),
      desc: form.crDesc.trim(),
      fit: form.crFit.slice(),
      status: +form.crStatus
    })
    if (!editing.id) {
      Object.assign(payload, {
        level: '简单',
        servings: 1,
        fiber: 0,
        rating: 0,
        views: 0,
        collects: 0,
        img: recipeChicken,
        ingredients: [{ name: '待完善', amount: '100', unit: 'g' }],
        steps: ['步骤待完善，可在后续版本补充。'],
        tips: ''
      })
    }
  } else if (type === 'article') {
    const title = form.caTitle.trim()
    if (!title) return toast('请填写文章标题', 'error')
    const tags = form.caTags.split(/[,，]/).map((x) => x.trim()).filter(Boolean)
    Object.assign(payload, {
      title,
      cat: form.caCat,
      author: form.caAuthor.trim() || '平台编辑部',
      tags,
      summary: form.caSummary.trim() || '内容整理中。',
      status: +form.caStatus
    })
    if (!editing.id) {
      const d = new Date()
      Object.assign(payload, {
        date:
          d.getFullYear() +
          '-' +
          String(d.getMonth() + 1).padStart(2, '0') +
          '-' +
          String(d.getDate()).padStart(2, '0'),
        cover: articleVegetables,
        views: 0,
        likes: 0,
        collects: 0,
        comments: 0,
        body: [{ t: 'p', text: payload.summary }]
      })
    }
  } else {
    const name = form.ciName.trim()
    if (!name) return toast('请填写食材名称', 'error')
    Object.assign(payload, {
      name,
      cat: form.ciCat,
      kcal: n0(form.ciKcal),
      p: n0(form.ciP),
      c: n0(form.ciC),
      f: n0(form.ciF),
      fiber: n0(form.ciFiber),
      desc: form.ciDesc.trim(),
      status: +form.ciStatus
    })
    if (!editing.id) {
      Object.assign(payload, { sugar: 0, sodium: 0, gi: 0, chol: 0, tags: [] })
    }
  }

  saving.value = true
  const res = await adminApi.contentSave(type, payload)
  saving.value = false
  if (res.code !== 200) return toast(res.message, 'error')
  contentOpen.value = false
  toast(res.message)
  loadContent(type)
}

/* ---------------- 发布通知 ---------------- */
const publishOpen = ref(false)
const publishing = ref(false)
const pub = reactive({ type: '系统', title: '', content: '', scope: 'all', userId: '' })

async function confirmPublish() {
  const title = pub.title.trim()
  const text = pub.content.trim()
  if (!title || !text) return toast('标题与内容不能为空', 'error')
  if (pub.scope === 'one' && !pub.userId.trim()) return toast('请填写指定用户 ID', 'error')

  publishing.value = true
  const res = await notificationsApi.publish({
    type: pub.type,
    title,
    content: text,
    userId: pub.userId.trim(),
    all: pub.scope === 'all'
  })
  publishing.value = false
  if (res.code !== 200) return toast(res.message, 'error')

  // 原版直接 DB.notifications.unshift()，这里走 store 才响应式
  store.publishNotif({ type: pub.type, title, content: text })
  publishOpen.value = false
  toast(res.message)
  pub.title = ''
  pub.content = ''
  pub.userId = ''
}

/* ---------------- 初始化 ---------------- */
onMounted(async () => {
  const res = await adminApi.overview()
  if (res.code !== 200) {
    toast(res.message, 'error')
    return
  }
  overview.value = res.data
  loadUsers()
})
</script>

<style scoped>
/* 以下全部来自静态版 admin.html 的页面级 <style>，只做搬移未改数值 */
.admin-top {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 20px;
}
@media (max-width: 1120px) {
  .admin-top {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
@media (max-width: 640px) {
  .admin-top {
    grid-template-columns: 1fr;
  }
}
.admin-chart {
  width: 100%;
  height: auto;
  display: block;
}
.stat-card .q-ico {
  width: 30px;
  height: 30px;
  border-radius: 9px;
  background: var(--green-050);
  color: var(--green-700);
  display: grid;
  place-items: center;
  flex: none;
}
.user-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}
.user-cell strong {
  display: block;
  font-size: 12.5px;
  color: var(--text);
  font-weight: 500;
}
.user-cell span {
  font-size: 11px;
  color: var(--text-3);
}
.table tr.disabled td {
  opacity: 0.55;
}
.status-dot {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 11.5px;
}
.status-dot i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--green-600);
}
.status-dot.off i {
  background: var(--text-3);
}
.admin-tabs-hd {
  overflow-x: auto;
}
.admin-tabs-hd .seg {
  flex: none;
}
.admin-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  padding: 16px 24px 0;
}
.admin-toolbar .search-box {
  flex: 1 1 220px;
  min-width: 190px;
}
.admin-toolbar .search-box .input {
  width: 100%;
  height: 36px;
}
.content-cell {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 220px;
}
.content-cell .thumb {
  width: 38px;
  height: 38px;
  border-radius: 9px;
  overflow: hidden;
  flex: none;
  background: var(--green-050);
  display: grid;
  place-items: center;
  color: var(--green-700);
  font-size: 12px;
}
.content-cell .thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.content-cell strong {
  display: block;
  font-size: 12.5px;
  color: var(--text);
  font-weight: 500;
}
.content-cell span.sub {
  display: block;
  margin-top: 2px;
  max-width: 320px;
  font-size: 11px;
  color: var(--text-3);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.table tr.off td {
  opacity: 0.55;
}
</style>
