const Token = artifacts.require("./Token.sol");

module.exports = function(deployer, network, accounts) {
    return deployer.then(()=>{
        return deployer.deploy(Token);
    });
}
