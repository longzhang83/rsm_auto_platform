/**
 * 判断是否为外部链接
 * @param path
 * @returns {boolean}
 */
export function isExternal(path) {
  return /^(https?:|mailto:|tel:)/.test(path)
}

/**
 * 验证用户名
 * @param username
 * @returns {boolean}
 */
export function validUsername(username) {
  return /^[a-zA-Z0-9_-]{4,16}$/.test(username)
}

/**
 * 验证邮箱
 * @param email
 * @returns {boolean}
 */
export function validEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

/**
 * 验证手机号
 * @param phone
 * @returns {boolean}
 */
export function validPhone(phone) {
  return /^1[3-9]\d{9}$/.test(phone)
}

/**
 * 验证密码强度
 * @param password
 * @returns {boolean}
 */
export function validPassword(password) {
  return password.length >= 8 && /[A-Za-z]/.test(password) && /\d/.test(password)
}