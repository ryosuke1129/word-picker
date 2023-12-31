# Word Picker on LINE OA
## はじめに
### 「Word Picker」の特徴
* OCR（Google Vision API）とGPT-4（Open AI API）を組み合わせたサービスです
* ChatGPT Plusでおなじみの「GPT-4」を使用しています
* 抽出したい項目名と画像を送信することで、欲しい情報のみをテキスト化して返してくれます

### 「Word Picker」の使い方
1. 項目名に「名前、住所、生年月日」を指定
2. 「免許証」の画像（スマホで撮影した写真でOK）を送信
3. Word Pickerが「免許証」から「名前、住所、生年月日」を探してテキストに起こして返信

### 「Word Picker」の友だち追加はこちらから
![S_gainfriends_2dbarcodes_GW](https://github.com/ryosuke1129/word-picker/assets/71242610/f2fc1b95-a8df-48c4-a79e-4a3afa68fd05)

<a href="https://lin.ee/3NHGiSd"><img src="https://scdn.line-apps.com/n/line_add_friends/btn/ja.png" alt="友だち追加" height="36" border="0"></a>

## 用意するもの
* Google Vision API
* OpenAI API
* LINE 公式アカウント
* LINE Messaging API
* AWS Lambda関数
* AWS DynamoDB（項目設定保存用）

## 構築手順
構築にあたり参考にした資料：<https://qiita.com/michitomo/items/a10465b12bcca32bf63a>

1. __Google Cloud Platformでキーを発行__
    * リンク：<https://console.cloud.google.com/>
2. __OpenAIでキーを発行__
    * リンク：<https://platform.openai.com/signup>
    * シークレットキー、オーガナイゼーションを控えておく
3. __LINE公式アカウント（Messaging API Channel）を開設、各種キーを発行__
    * リンク：<https://www.linebiz.com/jp/entry/>
    * チャンネルシークレット、チャンネルアクセストークンを控えておく
4. __AWSで新規のLambda関数を作成する__
    * ランタイムはPython3.10
    * API GWを通さず直接Lambda関数を叩けるようにするため、関数URLを有効にする（権限はNONE）
        * 作成した関数URLを、LINE公式アカウントのWebhook URLに設定する
    * 控えておいた各種キーを環境変数に設定する
    * デフォルトのタイムアウトが3秒と短いため、2分に設定を変更する
5. __AWSでDynamoDBを作成する__
    * 作成時の設定
        * パーティションキー：user_id（送信者のユーザーID）
        * ソートキー：timestamp（日付）
6. __Lambda関数をデプロイする__
    * 各種ライブラリを使用するため、カスタムレイヤーを追加する
        * （Docker、AWS CLI、AWS SAMを使って構築するため、超面倒・・・）
        * requirements.txtに沿って必要なライブラリをすべてインストールする
        * 参考：<https://nisshingeppo.com/ai/aws-lambda-library-install/>
    * ロールにDynamoDBへのアクセス権限を追加する
        * 追加するポリシー：AmazonDynamoDBFullAccess
    * lambda_function.pyに、作成したコードを貼り付けてデプロイする

## 作成者
* 作成者：K-Ryosuke
* Twitter：[@rsk_142](https://twitter.com/rsk_142)
