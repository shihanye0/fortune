import '@testing-library/jest-dom'
import { config } from '@vue/test-utils'
import ElementPlus from 'element-plus'

// 全局注册 Element Plus 组件供测试使用
config.global.plugins = [ElementPlus]
