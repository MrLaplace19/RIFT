error_login_or_password = {
    "type": "auth_fail",
    "payload": {"error": "Неверный логин или пароль"},
}
error_first_non_auth = {
    "type": "auth_fail",
    "payload": {"error": "Сначала пройдите авторизацию"},
}
error_user_offline = {"type": "error", "payload": {"error": "Пользователь не в сети"}}
error_user_exists = {
    "type": "register_fail",
    "payload": {"error": "Пользователь с таким именем уже существует"},
}
register_success = {
    "type": "register_success",
    "payload": {"message": "Вы успешно зарегистрировались"},
}