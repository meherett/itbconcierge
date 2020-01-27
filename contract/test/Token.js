const Token = artifacts.require("./Token.sol");

contract("Token", accounts => {
    const name = "ITB";
    const symbol = "ITB"
    const decimals = 18;

    it("confirm contract...", async () => {
        const TokenInstance = await Token.deployed();
        let tokenName = await TokenInstance.name();
        let tokenSymbol = await TokenInstance.symbol();
        let tokenDecimals = await TokenInstance.decimals();

        // 残高を取得してetherに変換
        let balance = await TokenInstance.balanceOf(accounts[0]);
        balance = web3.utils.fromWei(balance, "ether");

        assert.equal(tokenName, name, "Name isn't the same.")
        assert.equal(tokenSymbol, symbol, "Symbol isn't the same.")
        assert.equal(tokenDecimals, decimals, "Decimals isn't the same.")
        assert.equal(balance, 10000000000, "First account don't have 100億 MDR.");
    });
});
