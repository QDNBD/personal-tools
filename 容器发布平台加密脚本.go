func TestLogin(t *testing.T) {

	fmt.Println("====模拟注册====")
	var password = "996"                                                           //模拟注册是传递的密码
	hash, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost) //加密处理
	if err != nil {
		fmt.Println(err)
	}
	fmt.Println(string(hash))

	fmt.Println("====模拟登录====")
	// 密码验证
	err = bcrypt.CompareHashAndPassword([]byte("$2a$10$aFmt.vX9GkiCtP5MmF38tOwi1ReZYjgjwIvShTXJXpIAaq7FAuMbK"), []byte(password)) //验证（对比）
	if err != nil {
		fmt.Println("pwd wrong")
	} else {
		fmt.Println("pwd ok")
	}

}
