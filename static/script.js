class ThreadList extends React.Component {
    STR_NEW = 'new';
    STR_SUCCESS = 'completed';
    STR_FAILED = 'failed';
    URL_TOPIC_MODELING = 'topic_modeling/api/v1.0/posts';
    URL_WORD_CLOUD = 'tag_modeling/api/v1.0/posts';
    POSTS_SENTIMENT = 'sentiment/api/v1.0/posts';
    COMMENTS_SENTIMENT = 'sentiment/api/v1.0/comments';
    DASHBOARD_URL = 'thread/api/v1.0/dashboard';
    UPDATE_URL = 'thread/api/v1.0/update';
    ADD_FORM_URL = 'thread/api/v1.0/add';
    UPDATE_FORM_URL = 'thread/api/v1.0/update';
    GETDEEP_INFO_URL = 'https://painel.scopo.online/api/getdeep_info/get_sm_info';

    constructor(props) {
        super(props);
        this.state = {
            authToken: '',
            threadList: [],
            addModal: false,
        }
    }

    async componentWillMount() {
        setInterval(async () => {
            await this.getThreadList();
        }, 60000);
        await this.getThreadList();
    }

    async getThreadList() {
        const {data, status} = await axios.get(this.DASHBOARD_URL, {});
        if (status === 200) {
            this.setState({
                authToken: data['authorization_token'],
                threadList: data['data'],
            });
        }
    }

    async handleAddFormSubmit(e) {
        e.preventDefault();
        const self = this;
        let fData = {};

        $('#addForm').serializeArray().map(function (item) {
            fData[item.name] = item.value;
        });

        const headers = {
            'Authorization': `Token ${this.state.authToken}`,
            'Content-Type': 'application/json'
        };

        if (fData['type'] == 'facebook') {
            await axios.get(`${this.GETDEEP_INFO_URL}/?pg=${fData['name']}`, {
                headers: headers
            }).then((res) => {
                const {data} = res;
                data.length === 0 ? self.addSweetAlert(fData) : self.saveAddForm(fData);
            }).catch(function () {
                self.addSweetAlert(fData);
            });
        } else {
            self.saveAddForm(fData);
        }
    };

    async handleEditFormSubmit(e) {
        e.preventDefault();
        const self = this;
        let fData = {};
        let dataId = $('#editName').data('id');

        $('#editForm').serializeArray().map(function (item) {
            fData[item.name] = item.value;
        });

        const headers = {
            'Authorization': `Token ${this.state.authToken}`,
        };

        if (fData['type'] == 'facebook') {
            await axios.get(`${this.GETDEEP_INFO_URL}/?pg=${fData['name']}`, {
                headers: headers
            }).then((res) => {
                const {data} = res;
                data.length === 0 ? self.editSweetAlert(fData, dataId) : self.saveEditForm(fData, dataId);
            }).catch(function () {
                self.editSweetAlert(fData, dataId);
            });
        } else {
            self.saveEditForm(fData, dataId);
        }
    }

    async addSweetAlert(fData) {
        swal("The page is not authorized in our deep app. Please include the authorization on painel.scopo.online, Then api limit for this page will be used in our app.", {
            target: document.getElementById('addModal'),
            buttons: {
                cancel: "Cancel",
                catch: {
                    text: "Continue",
                    value: "catch",
                },
            },
        }).then((value) => {
            if (value === "catch") {
                this.saveAddForm(fData);
                swal("Success!", "Candidate Saved", "success");
            }
        });
    }

    editSweetAlert(fData, dataId) {
        swal("The page is not authorized in our deep app. Please include the authorization on painel.scopo.online, Then api limit for this page will be used in our app.", {
            target: document.getElementById('editModal'),
            buttons: {
                cancel: "Cancel",
                catch: {
                    text: "Continue",
                    value: "catch",
                },
            },
        }).then((value) => {
            if (value === "catch") {
                this.saveEditForm(fData, dataId);
                swal("Success!", "Candidate Saved", "success");
            }
        });
    }

    async saveAddForm(fData) {
        const {data, status} = await axios.post(this.ADD_FORM_URL, fData);
        if (status === 200) {
            this.setState({
                authToken: data['authorization_token'],
                threadList: data['data'],
            });
        }

        $('#addModal').modal('hide');
        $('#addForm')[0].reset();
    }

    async saveEditForm(fData, dataId) {
        const params = {
            id: dataId,
            update: {
                type: fData.type,
                user_id: fData.name,
                user_list: fData.complements
            }
        };

        const {data, status} = await axios.post(this.UPDATE_FORM_URL, params);

        if (status === 200) {
            this.setState({
                authToken: data['authorization_token'],
                threadList: data['data'],
            });
        }

        $('#editModal').modal('hide');
        $('#editForm')[0].reset();
    }

    handleEdit(e, thread) {
        e.preventDefault();
        const id = thread._id.$oid;

        $('#editModal').modal('show');
        $('#editName').val(thread.user_id);
        $('#editName').data('id', id);
        $('#editType').val(thread.type);

        if (thread.user_list) {
            $('#editComplements').val(thread.user_list.toString().split(",").slice(1).join(', '));
        }
    }

    showEdition(thread) {
        return (
            <button
                className="btn btn-primary p-1 mb-1 edition"
                onClick={e => this.handleEdit(e, thread)}
            >
                Edit
            </button>);
    }

    showPosts(postsData) {
        let posts = postsData.map((item, index) => {
            return (
                <React.Fragment key={item.user}>
                    <p style={{lineHeight: '25px', marginBottom: '0'}}>{item.user + ':' + item.posts}</p>
                </React.Fragment>
            );
        });
        return posts;
    }

    showComments(commentsData) {
        let posts = commentsData.map((item, index) => {
            return (
                <React.Fragment key={item.user}>
                    <p style={{lineHeight: '25px', marginBottom: '0'}}>{item.user + ':' + item.comments}</p>
                </React.Fragment>
            );
        });
        return posts;
    }

    showStatus(status, id, item_name) {
        let str_button = "RETRY";
        let badge_button = "badge-info";

        if (status === this.STR_NEW) {
            str_button = "TRY";
        }

        switch (status) {
            case this.STR_NEW:
                str_button = "TRY";
                break;
            case this.STR_SUCCESS:
                badge_button = "badge-success";
                break;
            case this.STR_FAILED:
                badge_button = "badge-danger";
        }

        return (
            <React.Fragment>
                <h6><span className={`badge ${badge_button} mt-2 p-1`}>{status.toString().toUpperCase()}</span></h6>
                <button type="button" className={'btn btn-primary retry p-1'}
                        onClick={e => this.handleReset(e, id, item_name)}>
                    {str_button}
                </button>
            </React.Fragment>
        )
    }

    showLockStatus(status, id, item_name) {
        let str_button = "";
        let lockList = ["LOCK", "UNLOCK"];
        let lock = '';

        if (status === false) {
            lock = 'lock-true';
            str_button = lockList[0];
            status = lockList[1];
        } else if (status === true) {
            str_button = lockList[1];
            status = lockList[0];
        }

        return (
            <React.Fragment>
                <h6><span className="badge badge-info mt-2 p-1">{status.toString().toUpperCase()}</span></h6>
                <button type="button" className={'btn btn-primary retry p-1 ' + lock}
                        onClick={e => this.handleReset(e, id, item_name)}>
                    {str_button}
                </button>
            </React.Fragment>
        )
    }

    async handleReset(e, id, name) {
        e.preventDefault();
        let value = "new";

        if (name === "lock") {
            value = e.target.className.includes('lock-true');
        }

        const params = {
            id: id,
            update: {
                [name]: value,
            }
        };

        const {data, status} = await axios.post(this.UPDATE_URL, params);

        if (status === 200) {
            this.setState({
                authToken: data['authorization_token'],
                threadList: data['data'],
            });
        }
    };

    showApiUrl(item) {
        let isDisabled = "disabled";
        let topic_modeling_url = this.URL_TOPIC_MODELING + '?name=' + item.user_id + '&type=' + item.type;
        let word_cloud_url = this.URL_WORD_CLOUD + '?name=' + item.user_id + '&type=' + item.type;
        let sentiment_url = this.POSTS_SENTIMENT + '?name=' + item.user_id + '&type=' + item.type;
        let comment_url = this.COMMENTS_SENTIMENT + '?candidate=' + item.user_id + '&limit=100&type=' + item.type;

        if (item.scrap_status === this.STR_SUCCESS && item.tokenize_status === this.STR_SUCCESS && item.lda_status === this.STR_SUCCESS) {
            isDisabled = ""
        }

        return (
            <React.Fragment>
                <a className={`btn btn-danger p-1 mb-1 link-api api-button ${isDisabled}`} href={topic_modeling_url}
                   target="blank">Topic Modeling</a> <br/>
                <a className={`btn btn-danger p-1 mb-1 link-api api-button ${isDisabled}`} href={word_cloud_url}
                   target="blank">Word Tag Cloud</a> <br/>
                <a className={`btn btn-danger p-1 mb-1 link-api api-button ${isDisabled}`} href={sentiment_url}
                   target="blank">Sentiment Posts</a> <br/>
                <a className={`btn btn-danger p-1 mb-1 link-api api-button ${isDisabled}`} href={comment_url}
                   target="blank">Sentiment Comments</a> <br/>
            </React.Fragment>
        );
    }

    showDate(sDate) {
        let value = "";

        if (sDate) {
            value = moment(new Date(sDate.$date)).format("YYYY/MM/DD") + '<br/>' + moment(new Date(sDate.$date)).format("hh:mm:ss")
        }
        return {__html: value};
    }

    render() {
        const {threadList} = this.state;
        return (
            <React.Fragment>
                <div className="modal fade" id="addModal" role="dialog">
                    <div className="modal-dialog">
                        <div className="modal-content">
                            <div className="modal-header">
                                <h4 className="modal-title">Add New Candidate</h4>
                                <button type="button" className="close" data-dismiss="modal">&times;</button>
                            </div>
                            <div className="modal-body offset-lg-1 col-lg-10">
                                <form id="addForm" onSubmit={e => this.handleAddFormSubmit(e)}>
                                    <div className="form-group row">
                                        <label htmlFor="userIdLabel" className="col-sm-3 col-form-label">Name</label>
                                        <div className="col-sm-9">
                                            <input type="text" className="form-control" name="name" id="name"
                                                   placeholder="Name"
                                                   required/>
                                        </div>
                                    </div>
                                    <div className="form-group row">
                                        <label htmlFor="snsTypeLabel" className="col-sm-3 col-form-label">SNS
                                            Type</label>
                                        <div className="col-sm-9">
                                            <select className="custom-select" name="type">
                                                <option value="facebook">Facebook</option>
                                                <option value="twitter">Twitter</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div className="form-group row">
                                        <label htmlFor="complementsLabel"
                                               className="col-sm-3 col-form-label">Complements</label>
                                        <div className="col-sm-9">
                                            <input type="text" className="form-control" name="complements"
                                                   id="complements"
                                                   placeholder="ex. Harry, John"/>
                                        </div>
                                    </div>
                                    <div className="form-group row">
                                        <div className="offset-8 col-sm-4">
                                            <button type="button" style={{fontSize: '13px'}}
                                                    className="btn btn-secondary mr-3"
                                                    data-dismiss="modal">
                                                Close
                                            </button>
                                            <button type="submit" style={{fontSize: '13px'}} className="btn btn-primary"
                                                    id="btnSave">
                                                Save Changes
                                            </button>
                                        </div>
                                    </div>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
                <div className="modal fade" id="editModal" role="dialog">
                    <div className="modal-dialog">
                        <div className="modal-content">
                            <div className="modal-header">
                                <h4 className="modal-title">Edit Candidate</h4>
                                <button type="button" className="close" data-dismiss="modal">&times;</button>
                            </div>
                            <div className="modal-body offset-lg-1 col-lg-10">
                                <form id="editForm" onSubmit={e => this.handleEditFormSubmit(e)}>
                                    <div className="form-group row">
                                        <label htmlFor="userIdLabel" className="col-sm-3 col-form-label">Name</label>
                                        <div className="col-sm-9">
                                            <input type="text" className="form-control" name="name" id="editName"
                                                   placeholder="Name"/>
                                        </div>
                                    </div>
                                    <div className="form-group row">
                                        <label htmlFor="snsTypeLabel" className="col-sm-3 col-form-label">SNS
                                            Type</label>
                                        <div className="col-sm-9">
                                            <select className="custom-select" name="type" id="editType">
                                                <option value="facebook">Facebook</option>
                                                <option value="twitter">Twitter</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div className="form-group row">
                                        <label htmlFor="complementsLabel"
                                               className="col-sm-3 col-form-label">Complements</label>
                                        <div className="col-sm-9">
                                            <input type="text" className="form-control" name="complements"
                                                   id="editComplements"
                                                   placeholder="ex. Harry, John"/>
                                        </div>
                                    </div>
                                    <div className="form-group row">
                                        <div className="offset-8 col-sm-4">
                                            <button type="button" style={{fontSize: '13px'}}
                                                    className="btn btn-secondary mr-3"
                                                    data-dismiss="modal">
                                                Close
                                            </button>
                                            <button type="submit" style={{fontSize: '13px'}} className="btn btn-primary"
                                                    id="btnSave">
                                                Save Changes
                                            </button>
                                        </div>
                                    </div>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
                <table className="table table-hover table-bordered table-striped text-center main-table">
                    <thead>
                    <tr>
                        <th scope="col">No</th>
                        <th scope="col">CANDIDATE</th>
                        <th scope="col">TYPE</th>
                        <th scope="col">COMPLEMENTS</th>
                        <th scope="col">POSTS<br/> SCRAPING</th>
                        <th scope="col">POSTS<br/> SENTIMENT</th>
                        <th scope="col">TOKENIZE</th>
                        <th scope="col">LDA</th>
                        <th scope="col">COMMENTS<br/> SCRAPING</th>
                        <th scope="col">COMMENTS<br/> SENTIMENT</th>
                        <th scope="col">LOCK</th>
                        <th scope="col">API</th>
                        <th scope="col">POSTS<br/> COUNTS</th>
                        <th scope="col">COMMENTS<br/> COUNTS</th>
                        <th scope="col">EDIT</th>
                        <th scope="col">START TIME</th>
                        <th scope="col">END TIME</th>
                    </tr>
                    </thead>
                    <tbody>
                    {
                        threadList.map(thread => (
                            <tr key={thread._id.$oid}>
                                <td>{thread.user_id}</td>
                                <td>{thread.type.charAt(0).toUpperCase() + thread.type.slice(1)}</td>
                                <td style={{lineHeight: '25px'}}
                                    dangerouslySetInnerHTML={{__html: thread.user_list.toString().split(",").slice(1).join('<br>')}}></td>
                                <td>{this.showStatus(thread.scrap_status, thread._id.$oid, 'scrap_status')}</td>
                                <td>{this.showStatus(thread.sentiment_status, thread._id.$oid, 'sentiment_status')}</td>
                                <td>{this.showStatus(thread.tokenize_status, thread._id.$oid, 'tokenize_status')}</td>
                                <td>{this.showStatus(thread.lda_status, thread._id.$oid, 'lda_status')}</td>
                                <td>{this.showStatus(thread.comments_scrap_status, thread._id.$oid, 'comments_scrap_status')}</td>
                                <td>{this.showStatus(thread.comments_sentiment_status, thread._id.$oid, 'comments_sentiment_status')}</td>
                                <td>{this.showLockStatus(thread.lock, thread._id.$oid, 'lock')}</td>
                                <td>{this.showApiUrl(thread)}</td>
                                <td>{this.showPosts(thread.posts)}</td>
                                <td>{this.showComments(thread.comments)}</td>
                                <td>{this.showEdition(thread)}</td>
                                <td dangerouslySetInnerHTML={this.showDate(thread.start_time)}></td>
                                <td dangerouslySetInnerHTML={this.showDate(thread.end_time)}></td>
                            </tr>
                        ))
                    }
                    </tbody>
                </table>
            </React.Fragment>
        )
    }
}

ReactDOM.render(<ThreadList/>, document.querySelector('.main-table'));
