import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

import { Component, useProps } from "@odoo/owl";


// PlusMoins : boutons - et + autour de la valeur, entre 1 et la valeur à l'ouverture
export class PlusMoins extends Component {
    static template = "is_jurabotec20.PlusMoins";
    props = useProps(standardFieldProps);

    setup() {
        this.maxi = this.value;
    }
    get value() {
        return this.props.record.data[this.props.name];
    }
    decrement() {
        var c = this.value - 1;
        if (c<1) c=1;
        this.updateValue(c);
    }
    increment() {
        var c = this.value + 1;
        if (c>this.maxi) c=this.maxi;
        this.updateValue(c);
    }
    async updateValue(value) {
        if (value !== this.value) {
            await this.props.record.update({ [this.props.name]: value });
        }
    }
}
registry.category("fields").add("plus_moins", { component: PlusMoins });
