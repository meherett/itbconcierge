pragma solidity ^0.5.0;

import "openzeppelin-solidity/contracts/token/ERC20/ERC20.sol";
import "openzeppelin-solidity/contracts/token/ERC20/ERC20Detailed.sol";

contract Token is ERC20, ERC20Detailed {
    string private _name = "ITB";
    string private _symbol = "ITB";
    uint8 private _decimals = 18;
    uint value = 10000000000e18;

    constructor()
        ERC20Detailed(_name, _symbol, _decimals)
        public
    {
        _mint(msg.sender, value);
    }
}
