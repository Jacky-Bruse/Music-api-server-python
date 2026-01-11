def convert_dict_to_form(dic: dict) -> str:
    return "&".join([f"{k}={v}" for k, v in dic.items()])
