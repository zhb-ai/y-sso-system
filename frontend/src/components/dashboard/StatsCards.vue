<template>
  <div class="stats-cards">
    <template v-if="loading">
      <el-card v-for="i in 4" :key="i" shadow="hover" class="stat-card">
        <div class="stat-content">
          <div class="stat-info">
            <el-skeleton animated :rows="1" />
            <el-skeleton animated :rows="1" />
          </div>
          <div class="stat-icon skeleton-icon">
            <el-skeleton animated :rows="1" />
          </div>
        </div>
      </el-card>
    </template>
    <template v-else>
      <el-card shadow="hover" class="stat-card">
        <div class="stat-content">
          <div class="stat-info">
            <h3>{{ applicationCount }}</h3>
            <p>已注册应用</p>
          </div>
          <div class="stat-icon application">
            <el-icon><Grid /></el-icon>
          </div>
        </div>
      </el-card>

      <el-card shadow="hover" class="stat-card">
        <div class="stat-content">
          <div class="stat-info">
            <h3>{{ userCount }}/{{ totalUserCount }}</h3>
            <p>日活用户/总用户</p>
          </div>
          <div class="stat-icon user">
            <el-icon><User /></el-icon>
          </div>
        </div>
      </el-card>

      <el-card shadow="hover" class="stat-card">
        <div class="stat-content">
          <div class="stat-info">
            <h3>{{ employeeCount }}</h3>
            <p>员工数量</p>
          </div>
          <div class="stat-icon role">
            <el-icon><Management /></el-icon>
          </div>
        </div>
      </el-card>

      <el-card shadow="hover" class="stat-card">
        <div class="stat-content">
          <div class="stat-info">
            <h3>{{ departmentCount }}</h3>
            <p>部门数量</p>
          </div>
          <div class="stat-icon department">
            <el-icon><OfficeBuilding /></el-icon>
          </div>
        </div>
      </el-card>
    </template>
  </div>
</template>

<script setup>
import { Grid, Management, OfficeBuilding, User } from "@element-plus/icons-vue";

defineProps({
  loading: { type: Boolean, default: false },
  applicationCount: { type: [Number, String], default: 0 },
  userCount: { type: [Number, String], default: 0 },
  totalUserCount: { type: [Number, String], default: 0 },
  employeeCount: { type: [Number, String], default: 0 },
  departmentCount: { type: [Number, String], default: 0 },
});
</script>
