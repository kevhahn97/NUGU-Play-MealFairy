const mysql = require('mysql')
const request = require('request')
const _ = require('lodash')
const serverCredentials = require('./credentials.json')

var connection = mysql.createConnection(serverCredentials)

class Response {
    constructor(req) {
        this.version = req.version
        this.resultCode = 'OK' //can be modified later
        this.output = {}
        
        //set given Parameters to response
        if(req.action.parameters.food != undefined){
            this.setParameters({
                food: req.action.parameters.food.value
            })
        }
    }

    async getID(req, res) {
        return new Promise((resolve, reject) => {
            if (req.context.session.accessToken == undefined) {
                res.setParameters({
                    ID: 'null'
                })
                resolve()
            }
            else {
                var at = req.context.session.accessToken

                var options = {
                    uri: 'https://www.googleapis.com/oauth2/v2/userinfo',
                    method: 'GET',
                    headers: {
                        Authorization: 'Bearer ' + at
                    }
                }

                request(options, function (error, response, body) {
                    if (error || (JSON.parse(body).id == undefined)) {
                        //set errorcode to accessToken invalidated
                        console.log(error)
                        reject(new Error('loginfail'))
                    }
                    else {
                        res.setParameters({
                            ID: JSON.parse(body).id
                        })
                        resolve()
                    }
                })
                //res.setParameters({ID: '123'})
                //resolve()
            }
        })
    }

    async setFoodStatus(req, res) {
        return new Promise((resolve, reject) => {
            if (req.action.parameters.food == undefined) {
                res.setParameters({
                    status: 'nofood',
                    foodlist: 'null'
                })
                resolve()
            }
            else {
                var p_food = req.action.parameters.food.value
                var ptype_food = req.action.parameters.food.type

                if (ptype_food == 'FOOD') {
                    connection.query('select * from food where food = ?', [p_food], (err, rows, fields) => {
                        if(err){
                            console.log(err)
                            res.resultCode = 'DBerror'
                            resolve()
                        }
                        else{
                            if(rows[0] != undefined){
                                res.setParameters({
                                    status: 'food',
                                    foodlist: 'null'
                                })
                            }
                            else{
                                res.setParameters({
                                    status: 'notready',
                                    foodlist: 'null'
                                })
                            }
                            resolve()
                        }
                    })
                }
                else if (ptype_food == 'FOODGROUP') {
                    connection.query('select * from food where foodgroup = ?', [p_food], (err, rows, fields) => {
                        if(err){
                            res.resultCode = 'DBerror'
                            resolve()
                        }
                        else{
                            var list = []
                            rows.forEach(element => {
                                list.push(element.food)
                            })
                            res.setParameters({
                                status: 'foodgroup',
                                foodlist: list.join(', ')
                            })
                            resolve()
                        }
                    })
                }
            }
        })
    }

    setParameters(outputKeyAndValues) { //overwrites an object if already exists. Otherwise, it appends the given object.
        this.output = _.assign(this.output, outputKeyAndValues)
    }
}

exports.handler = async (event) => {
    var response = new Response(event)
    await response.getID(event, response)
    await response.setFoodStatus(event, response)
    return response
};