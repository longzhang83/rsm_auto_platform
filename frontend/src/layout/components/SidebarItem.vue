<template>
  <div v-if="!item.meta?.hidden">
    <template v-if="hasOneShowingChild(item.children, item) && (!onlyOneChild.children || onlyOneChild.noShowingChildren) && !item.meta?.alwaysShow">
      <app-link v-if="onlyOneChild.meta" :to="resolvePath(onlyOneChild.path)">
        <el-menu-item :index="resolvePath(onlyOneChild.path)" :class="{ 'submenu-title-noDropdown': !isNest }">
          <el-icon v-if="onlyOneChild.meta.icon">
            <component :is="onlyOneChild.meta.icon" />
          </el-icon>
          <template #title>
            <span>{{ onlyOneChild.meta.title }}</span>
            <el-tag v-if="onlyOneChild.meta.disabled" type="info" size="small" class="ml-2">开发中</el-tag>
          </template>
        </el-menu-item>
      </app-link>
    </template>

    <el-sub-menu v-else ref="subMenu" :index="resolvePath(item.path)" popper-append-to-body>
      <template #title>
        <el-icon v-if="item.meta?.icon">
          <component :is="item.meta.icon" />
        </el-icon>
        <span>{{ item.meta?.title }}</span>
      </template>

      <sidebar-item
        v-for="child in item.children"
        :key="child.path"
        :is-nest="true"
        :item="child"
        :base-path="resolvePath(item.path)"
      />
    </el-sub-menu>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { isExternal } from '@/utils/validate'
import AppLink from './Link.vue'

const props = defineProps({
  item: {
    type: Object,
    required: true
  },
  isNest: {
    type: Boolean,
    default: false
  },
  basePath: {
    type: String,
    default: ''
  }
})

const subMenu = ref(null)

const onlyOneChild = ref(null)

const hasOneShowingChild = (children = [], parent) => {
  const showingChildren = children.filter(item => {
    if (item.meta?.hidden) {
      return false
    } else {
      // 临时设置
      onlyOneChild.value = item
      return true
    }
  })

  // 当只有一个子路由时，默认显示该子路由
  if (showingChildren.length === 1) {
    return true
  }

  // 没有子路由则显示父路由本身
  if (showingChildren.length === 0) {
    // 保留原始路径，不要设置为空字符串
    onlyOneChild.value = { ...parent, noShowingChildren: true }
    return true
  }

  return false
}

const resolvePath = (routePath) => {
  if (isExternal(routePath)) {
    return routePath
  }
  if (isExternal(props.basePath)) {
    return props.basePath
  }

  // If basePath is already the full path (for top-level routes), just return it
  if (props.basePath && !routePath) {
    return props.basePath
  }

  // For nested routes, construct the proper path
  if (routePath) {
    // If routePath starts with '/', it's an absolute path
    if (routePath.startsWith('/')) {
      return routePath
    }

    // If basePath exists and is not root, concatenate properly
    if (props.basePath && props.basePath !== '/') {
      // Remove trailing slash from basePath if exists
      const cleanBasePath = props.basePath.endsWith('/')
        ? props.basePath.slice(0, -1)
        : props.basePath
      return cleanBasePath + '/' + routePath
    }

    // Otherwise, add leading slash for root level routes
    return '/' + routePath
  }

  return '/'
}
</script>

<style scoped>
.submenu-title-noDropdown {
  @apply !important;
}

/* 一级菜单项样式 */
.el-menu-item {
  margin: 4px 8px;
  border-radius: 10px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-weight: 500;
  height: 48px;
  line-height: 48px;
  color: var(--neutral-700);
  position: relative;
  border: 1px solid transparent;
}

.el-menu-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 0;
  background: var(--primary-600);
  border-radius: 0 2px 2px 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.el-menu-item:hover {
  background: linear-gradient(135deg, var(--primary-50) 0%, var(--primary-100) 100%) !important;
  color: var(--primary-700);
  border-color: var(--primary-200);
  transform: translateX(4px);
}

.el-menu-item:hover::before {
  height: 20px;
}

.el-menu-item.is-active {
  background: linear-gradient(135deg, var(--primary-600) 0%, var(--primary-700) 100%) !important;
  color: white;
  box-shadow: 0 4px 16px rgba(0, 149, 215, 0.25);
  border-color: var(--primary-500);
  transform: translateX(4px);
}

.el-menu-item.is-active::before {
  height: 24px;
  background: white;
}

/* 子菜单标题样式 */
.el-sub-menu :deep(.el-sub-menu__title) {
  margin: 4px 8px;
  border-radius: 10px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-weight: 500;
  height: 48px;
  line-height: 48px;
  color: var(--neutral-700);
  position: relative;
  border: 1px solid transparent;
}

.el-sub-menu :deep(.el-sub-menu__title::before) {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 0;
  background: var(--primary-600);
  border-radius: 0 2px 2px 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.el-sub-menu :deep(.el-sub-menu__title:hover) {
  background: linear-gradient(135deg, var(--primary-50) 0%, var(--primary-100) 100%) !important;
  color: var(--primary-700);
  border-color: var(--primary-200);
  transform: translateX(4px);
}

.el-sub-menu :deep(.el-sub-menu__title:hover::before) {
  height: 20px;
}

.el-sub-menu.is-opened :deep(.el-sub-menu__title) {
  background: linear-gradient(135deg, var(--primary-50) 0%, var(--primary-100) 100%) !important;
  color: var(--primary-700);
  border-color: var(--primary-200);
}

.el-sub-menu.is-opened :deep(.el-sub-menu__title::before) {
  height: 20px;
}

/* 嵌套子菜单项样式（二级及以下） */
.el-sub-menu :deep(.el-menu-item) {
  margin: 2px 8px 2px 16px;
  border-radius: 8px;
  height: 40px;
  line-height: 40px;
  font-size: 14px;
  padding-left: 40px !important;
  background: transparent;
}

.el-sub-menu :deep(.el-menu-item::before) {
  display: none;
}

.el-sub-menu :deep(.el-menu-item:hover) {
  background: var(--primary-50) !important;
  color: var(--primary-600);
  transform: translateX(2px);
}

.el-sub-menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(135deg, var(--primary-100) 0%, var(--primary-200) 100%) !important;
  color: var(--primary-700);
  font-weight: 600;
  box-shadow: none;
  border-left: 3px solid var(--primary-600);
  transform: translateX(0);
}

/* 嵌套子菜单容器 */
.el-sub-menu :deep(.el-menu) {
  background-color: var(--neutral-50);
  border-radius: 8px;
  margin: 4px 8px;
  padding: 4px 0;
}

/* 图标样式 */
.el-menu-item :deep(.el-icon),
.el-sub-menu :deep(.el-sub-menu__title .el-icon) {
  width: 20px;
  height: 20px;
  margin-right: 8px;
  transition: all 0.2s ease;
}

.el-menu-item:hover :deep(.el-icon),
.el-sub-menu :deep(.el-sub-menu__title:hover .el-icon) {
  transform: scale(1.1);
}

/* 嵌套菜单的展开箭头 */
.el-sub-menu :deep(.el-sub-menu__icon-arrow) {
  transition: transform 0.3s ease;
}

.el-sub-menu.is-opened :deep(.el-sub-menu__icon-arrow) {
  transform: rotate(180deg);
}

/* 收缩状态下隐藏所有文本和标签 - 针对多级菜单优化 */
:deep(.el-menu--collapse) {
  /* 隐藏一级菜单项的文本和标签 */
  .el-menu-item span,
  .el-menu-item .el-tag {
    display: none !important;
    width: 0 !important;
    height: 0 !important;
    overflow: hidden !important;
  }

  /* 隐藏子菜单标题的文本内容 */
  .el-sub-menu__title span {
    display: none !important;
    width: 0 !important;
    height: 0 !important;
    overflow: hidden !important;
  }

  /* 隐藏子菜单的展开箭头 */
  .el-sub-menu__icon-arrow {
    display: none !important;
  }

  /* 收缩时菜单项居中显示图标 */
  .el-menu-item {
    padding: 0 !important;
    text-align: center !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
  }

  .el-sub-menu__title {
    padding: 0 !important;
    text-align: center !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
  }

  /* 收缩时图标不需要右边距 */
  .el-menu-item .el-icon,
  .el-sub-menu__title .el-icon {
    margin-right: 0 !important;
  }
}
</style>