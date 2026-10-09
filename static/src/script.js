/** @odoo-module **/
const {Component} = owl;

import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { registry } from "@web/core/registry";


// PlusMoins
export class PlusMoins extends Component {
    setup() {
        super.setup();
        this.maxi = this.props.value;
    }
    decrement() {
        var c = this.props.value - 1;
        if (c<1) c=1;
        this.props.value = c;
        this.updateValue();
    }
    increment() {
        console.log("maxi=",this.maxi);
        var c = this.props.value + 1;
        if (c>this.maxi) c=this.maxi;
        this.props.value = c;
        this.updateValue();
    }
    /**
     * Checks if the current value is different from the last saved value.
     * If the field is dirty it needs to be saved.
     * @returns {boolean}
     */
    _isDirty() {
        console.log("_isDirty",this.props.readonly,this.props.value,this.getEditorValue())
        return !this.props.readonly && this.props.value !== this.getEditorValue();
    }
    async updateValue() {
        const value = this.props.value;
        const lastValue = (this.props.value || "").toString();
        if (value !== null && !(!lastValue && value === "") && value !== lastValue) {
            if (this.props.setDirty) {
                this.props.setDirty(true);
            }
            await this.props.update(value);
        }
    }
}
PlusMoins.template = "is_jurabotec.PlusMoins";
PlusMoins.props = standardFieldProps;
registry.category("fields").add("plus_moins", PlusMoins);



// PlusMoins10
export class PlusMoins10 extends Component {
    setup() {
        super.setup();
    }
    decrement() {
        var c = this.props.value - 1;
        if (c<0) c=0;
        this.props.value = c;
        this.updateValue();
    }
    decrement10() {
        var c = this.props.value - 10;
        if (c<0) c=0;
        this.props.value = c;
        this.updateValue();
    }
    increment() {
        console.log("maxi=",this.maxi);
        var c = this.props.value + 1;
        this.props.value = c;
        this.updateValue();
    }
    increment10() {
        console.log("maxi=",this.maxi);
        var c = this.props.value + 10;
        this.props.value = c;
        this.updateValue();
    }
    /**
     * Checks if the current value is different from the last saved value.
     * If the field is dirty it needs to be saved.
     * @returns {boolean}
     */
    _isDirty() {
        console.log("_isDirty",this.props.readonly,this.props.value,this.getEditorValue())
        return !this.props.readonly && this.props.value !== this.getEditorValue();
    }
    async updateValue() {
        const value = this.props.value;
        const lastValue = (this.props.value || "").toString();
        if (value !== null && !(!lastValue && value === "") && value !== lastValue) {
            if (this.props.setDirty) {
                this.props.setDirty(true);
            }
            await this.props.update(value);
        }
    }
}
PlusMoins10.template = "is_jurabotec.PlusMoins10";
PlusMoins10.props = standardFieldProps;
registry.category("fields").add("plus_moins10", PlusMoins10);




