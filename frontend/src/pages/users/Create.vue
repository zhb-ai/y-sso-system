<template>
  <el-dialog
    v-model="visible"
    title="新建用户"
    width="600px"
    align-center
    destroy-on-close
    @close="handleClose"
  >
    <div class="section-blocks" style="gap: 0;">
      <div class="section-block">
        <div class="section-block__header">
          <div class="section-block__title">
            <el-icon><User /></el-icon>
            <span>基本信息</span>
          </div>
        </div>
        <div class="section-block__content">
          <el-form :model="userForm" :rules="userRules" ref="userFormRef" label-width="80px">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="用户名" prop="username">
                  <el-input v-model="userForm.username" placeholder="请输入用户名" autocomplete="off" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="姓名" prop="name">
                  <el-input v-model="userForm.name" placeholder="请输入姓名" autocomplete="off" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="邮箱" prop="email">
                  <el-input v-model="userForm.email" placeholder="请输入邮箱（选填）" autocomplete="off" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="手机号" prop="phone">
                  <el-input
                    v-model="userForm.phone"
                    placeholder="请输入手机号"
                    autocomplete="new-phone"
                    :input-attrs="{ autocomplete: 'new-phone', 'data-lpignore': 'true' }"
                  />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="密码" prop="password">
                  <el-input
                    v-model="userForm.password"
                    type="password"
                    placeholder="请输入初始密码"
                    show-password
                    autocomplete="new-password"
                    :input-attrs="{ autocomplete: 'new-password' }"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="状态" prop="status">
                  <el-switch
                    v-model="userForm.status"
                    active-value="active"
                    inactive-value="inactive"
                    :active-action-icon="Check"
                    :inactive-action-icon="Close"
                    active-text="启用"
                    inactive-text="禁用"
                    inline-prompt
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </div>
      </div>
    </div>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleCancel">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">确定</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Check, Close } from '@element-plus/icons-vue'
import { userApi } from '@/api'
import { handleApiError, getDefaultErrorMessage } from '@/utils/errorHandler'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

const visible = ref(false)
const userFormRef = ref(null)
const submitLoading = ref(false)

// 表单数据
const userForm = reactive({
  username: '',
  name: '',
  email: '',
  phone: '',
  password: '',
  status: 'active'
})

// 表单验证规则
const userRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 1, max: 20, message: '用户名长度在 1 到 20 个字符', trigger: 'blur' },
    { 
      validator: (rule, value, callback) => {
        if (!value) {
          callback(new Error('请输入用户名'))
        } else if (!/^[一-龥a-zA-Z0-9_]+$/.test(value)) {
          callback(new Error('用户名只能包含中文、字母、数字、下划线'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  name: [
    { required: true, message: '请输入姓名', trigger: 'blur' },
    { min: 2, max: 20, message: '姓名长度在 2 到 20 个字符', trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
  ]
}

// 监听modelValue变化
watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val) {
    resetForm()
  }
})

// 监听visible变化
watch(visible, (val) => {
  emit('update:modelValue', val)
})

// 重置表单
const resetForm = () => {
  Object.assign(userForm, {
    username: '',
    name: '',
    email: '',
    phone: '',
    password: '',
    status: 'active'
  })
}

// 提交表单
const handleSubmit = async () => {
  if (!userFormRef.value) return
  
  try {
    await userFormRef.value.validate()
    submitLoading.value = true

    await userApi.create(userForm)
    ElMessage.success('用户创建成功')
    
    visible.value = false
    emit('success')
  } catch (error) {
    if (error !== 'cancel') {
      handleApiError(error, getDefaultErrorMessage('create'))
    }
  } finally {
    submitLoading.value = false
  }
}

// 取消
const handleCancel = () => {
  visible.value = false
}

// 关闭对话框
const handleClose = () => {
  resetForm()
}
</script>