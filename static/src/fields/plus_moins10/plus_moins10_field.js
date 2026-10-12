import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

import { Component, useProps } from "@odoo/owl";


// PlusMoins10 : boutons -10, -, + et +10 autour de la valeur, minimum 0
export class PlusMoins10 extends Component {
    static template = "is_jurabotec20.PlusMoins10";
    props = useProps(standardFieldProps);

    get value() {
        return this.props.record.data[this.props.name];
    }
    decrement() {
        var c = this.value - 1;
        if (c<0) c=0;
        this.updateValue(c);
    }
    decrement10() {
        var c = this.value - 10;
        if (c<0) c=0;
        this.updateValue(c);
    }
    increment() {
        this.updateValue(this.value + 1);
    }
    increment10() {
        this.updateValue(this.value + 10);
    }
    async updateValue(value) {
        if (value !== this.value) {
            await this.props.record.update({ [this.props.name]: value });
        }
    }
}
registry.category("fields").add("plus_moins10", { component: PlusMoins10 });
