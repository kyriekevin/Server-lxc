# docker 镜像制作说明
1. 数据集路径: ```/home/algo/test_dataset```
2. 程序运行路径: ```/home/prog/run.sh```
3. 推理结果路径: ```/home/prog/result```

# 推理结果格式
```
{
    "image_name": "000000", 
    "objects": [
        {
            "x": ,
            "y": ,
            "width": ,
            "height": ,
            "attribute": ""
        },
        {
            "x": ,
            "y": ,
            "width": ,
            "height": ,
            "attribute": ""
        },
    ]
}
```

## 说明
1. image_name 不需要带图片扩展名(jpeg,jpg)
2. attribute 为缺陷类型，填规定字母表示
3. x, y 为检测框左上顶点坐标
4. 一个图片对应一个json结果，分开存储在推理结果文件夹下，文件名为对应图片名(000000.json)
