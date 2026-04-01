import React from "react";
import '../App.css';

// 1. Define FormattedMoney helper
const FormattedMoney = (props) => {
   return <span>₦{props.value.toLocaleString()}</span>;
}

// 2. Define FormattedDate helper
const FormattedDate = (props) => {
   return <span>{props.value.toLocaleDateString()}</span>;
}

const ExpenseEntryItem = (props) =>{

      // Safety check: prevent crash if item is missing
      if (!props.item) return null;
      return (
         <div className="item-container">
            <div><b>Item:</b> <em>{props.item.name}</em></div>
            <div><b>Amount:</b> 
               <em><FormattedMoney value={props.item.amount} /></em>
            </div>
            <div><b>Spend Date:</b> 
               <em><FormattedDate value={props.item.spendDate} /></em>
            </div>
            <div><b>Category:</b> 
               <em>{props.item.category}</em></div>
         </div>
      );
   }
export default ExpenseEntryItem;