# ITB ERC20 Token

ERC20トークンを発行する。

## Environment
```
Node v12.0.0
Web3.js v1.2.1
solidity-0.5.0
truffle@5.0.33
openzeppelin-solidity@2.3.0
ganache-cli@6.6.0
```

## Setup

```
npm install -g truffle@5.0.33
npm install -g ganache-cli@6.6.0
npm install
```

.secretファイルにウォレットのパスフレーズを記載(localの場合は必要なし)
.infuraKeyファイルに接続するネットワークのinfuraのIDを記載(localの場合は必要なし)

truffle-config.jsのgasとgasPriceは適切な値をetherscanなどで確認してセットする。
https://etherscan.io/

## Test

### local環境
```
ganache-cli
truffle test --network development
```

### Testnet Ropsten
デプロイされるので注意
```
truffle test --network ropsten
```

## Migrate and Deploy
networkを用途によって変更
```
truffle migrate --network ropsten
```
