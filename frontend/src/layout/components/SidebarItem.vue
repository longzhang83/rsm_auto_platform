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
        :base-path="resolvePath(child.path)"
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

  // 没有子路由则显示父路由
  if (showingChildren.length === 0) {
    onlyOneChild.value = { ...parent, path: '', noShowingChildren: true }
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
    return '/' + routePath
  }

  return '/'
}
</script>

<style scoped>
.submenu-title-noDropdown {
  @apply !important;
}

.el-menu-item {
  @apply text-gray-300 hover:text-white hover:bg-gray-700;
}

.el-menu-item.is-active {
  @apply bg-gray-700 text-white border-r-2 border-brand-500;
}

.el-sub-menu :deep(.el-sub-menu__title) {
  @apply text-gray-300 hover:text-white hover:bg-gray-700;
}

.el-sub-menu.is-opened :deep(.el-sub-menu__title) {
  @apply text-white bg-gray-700;
}
</style>